use anyhow::{Context, Result};
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::sync::mpsc::Sender;

/// Commands the resident daemon accepts on its unix socket.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Show,
    Hide,
    Toggle,
    Reload,
    Quit,
    /// Capture the framebuffer to a PNG. Debug aid: it does not need macOS screen recording
    /// permission because it reads our own render target rather than the display.
    Screenshot,
}

impl Command {
    pub fn parse(value: &str) -> Option<Command> {
        match value.trim() {
            "show" => Some(Command::Show),
            "hide" => Some(Command::Hide),
            "toggle" => Some(Command::Toggle),
            "reload" => Some(Command::Reload),
            "quit" => Some(Command::Quit),
            "screenshot" => Some(Command::Screenshot),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Command::Show => "show",
            Command::Hide => "hide",
            Command::Toggle => "toggle",
            Command::Reload => "reload",
            Command::Quit => "quit",
            Command::Screenshot => "screenshot",
        }
    }
}

/// Send a command to a running daemon. Returns an error if no daemon is listening.
pub fn send(command: Command) -> Result<()> {
    let socket = ps_core::paths::daemon_socket();
    let mut stream = UnixStream::connect(&socket)
        .with_context(|| format!("no daemon listening on {}", socket.display()))?;
    stream.write_all(command.as_str().as_bytes())?;
    stream.write_all(b"\n")?;
    Ok(())
}

/// Bind the socket and forward commands to the UI thread.
///
/// The listener runs on its own thread; `wake` is called after every command so the egui event
/// loop comes out of its idle wait immediately rather than at the next natural repaint.
pub fn listen(sender: Sender<Command>, wake: impl Fn() + Send + 'static) -> Result<()> {
    let socket = ps_core::paths::daemon_socket();
    if let Some(parent) = socket.parent() {
        std::fs::create_dir_all(parent)?;
    }

    // A socket file left behind by a crashed daemon would block the bind.
    if socket.exists() {
        if UnixStream::connect(&socket).is_ok() {
            anyhow::bail!("a daemon is already running on {}", socket.display());
        }
        std::fs::remove_file(&socket)?;
    }

    let listener = UnixListener::bind(&socket)
        .with_context(|| format!("could not bind {}", socket.display()))?;

    std::thread::spawn(move || {
        for stream in listener.incoming() {
            let Ok(stream) = stream else { continue };
            let mut line = String::new();
            if BufReader::new(stream).read_line(&mut line).is_err() {
                continue;
            }
            let Some(command) = Command::parse(&line) else {
                continue;
            };
            if sender.send(command).is_err() {
                break;
            }
            wake();
        }
    });

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::Command;

    #[test]
    fn every_command_survives_the_socket_round_trip() {
        for command in [
            Command::Show,
            Command::Hide,
            Command::Toggle,
            Command::Reload,
            Command::Quit,
            Command::Screenshot,
        ] {
            assert_eq!(Command::parse(&format!("{}\n", command.as_str())), Some(command));
        }
    }

    #[test]
    fn unknown_commands_are_ignored() {
        assert_eq!(Command::parse("open"), None);
        assert_eq!(Command::parse(""), None);
    }
}
