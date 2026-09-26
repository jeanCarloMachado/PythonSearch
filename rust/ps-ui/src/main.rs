mod app;
mod daemon;
mod theme;

use anyhow::Result;
use app::{Launcher, Outcome};
use daemon::Command;
use eframe::egui;
use raw_window_handle::HasWindowHandle;
use ps_core::{Actions, Index, UsageStats};
use std::io::Write;
use std::process::{Child, Stdio};
use std::sync::mpsc::{channel, Receiver};
use std::sync::{Arc, Mutex};
use theme::Metrics;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.first().map(String::as_str) {
        // The launch path. Kept first and trivial: this is what the hotkey runs.
        Some("show") => client(Command::Show),
        Some("hide") => client(Command::Hide),
        Some("toggle") => client(Command::Toggle),
        Some("reload") => client(Command::Reload),
        Some("quit") => client(Command::Quit),
        Some("screenshot") => client(Command::Screenshot),
        Some("daemon") if cfg!(target_os = "macos") => run(true, load_index()?),
        Some("daemon") => window_daemon(),
        Some("ui") if args.get(1).map(String::as_str) == Some("--entries-stdin") => {
            NOTIFY_DAEMON_ON_RELOAD.store(true, std::sync::atomic::Ordering::Relaxed);
            run(false, read_index_from_stdin()?)
        }
        Some("ui") | None => run(false, load_index()?),
        Some("search") => search(&args[1..].join(" ")),
        Some(other) => {
            eprintln!("unknown command: {other}");
            eprintln!("usage: ps [daemon|show|hide|toggle|reload|quit|ui|search <query>]");
            std::process::exit(2);
        }
    }
}

/// Poke a running daemon and exit. Deliberately does no other work: this process is on the
/// critical path between the hotkey and the window appearing.
fn client(command: Command) -> Result<()> {
    daemon::send(command)
}

fn load_index() -> Result<Index> {
    Ok(Index::from_entries(Actions::resolve().load_entries()?))
}

/// Entries for a window started by the Linux daemon arrive on stdin, already loaded.
fn read_index_from_stdin() -> Result<Index> {
    let mut json = Vec::new();
    std::io::Read::read_to_end(&mut std::io::stdin(), &mut json)?;
    Ok(Index::from_entries(ps_core::actions::parse_entries(&json)?))
}

/// Set in windows started by the Linux daemon, whose own reload must also refresh the daemon's copy.
static NOTIFY_DAEMON_ON_RELOAD: std::sync::atomic::AtomicBool =
    std::sync::atomic::AtomicBool::new(false);

fn run(as_daemon: bool, index: Index) -> Result<()> {
    // Entries are loaded once, before this, into memory. Nothing on the search path ever reads a
    // file or spawns a process.
    if std::env::var("PS_DEBUG").is_ok() {
        eprintln!("loaded {} entries", index.len());
    }

    let (command_sender, command_receiver) = channel::<Command>();
    let pending_index: Arc<Mutex<Option<Index>>> = Arc::new(Mutex::new(None));
    let wake_handle: Arc<Mutex<Option<egui::Context>>> = Arc::new(Mutex::new(None));

    if as_daemon {
        let wake = wake_handle.clone();
        daemon::listen(command_sender.clone(), move || {
            if let Some(ctx) = wake.lock().unwrap().as_ref() {
                ctx.request_repaint();
            }
        })?;
    }

    // Open at the height of the empty-query listing. On Wayland a resize sent on the first frame,
    // before the compositor has configured the surface, is dropped, which left only the search row
    // on screen with the results cut off below it.
    let initial_height = Metrics::window_height(index.len().min(Metrics::MAX_VISIBLE_ROWS));

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([Metrics::WINDOW_WIDTH, initial_height])
            .with_decorations(false)
            .with_transparent(true)
            .with_resizable(false)
            .with_visible(!as_daemon),
        // AppKit places the panel itself; elsewhere ask the platform to centre it.
        centered: cfg!(not(target_os = "macos")),
        ..Default::default()
    };

    let pending_for_app = pending_index.clone();
    let wake_for_app = wake_handle.clone();

    eframe::run_native(
        "PythonSearch",
        options,
        Box::new(move |cc| {
            theme::install(&cc.egui_ctx);
            *wake_for_app.lock().unwrap() = Some(cc.egui_ctx.clone());

            ps_mac::hide_from_dock();

            let mut index = index;
            // Usage history is ~19 MB across thousands of small files; loading it inline would
            // delay the first frame for no good reason.
            let usage_ctx = cc.egui_ctx.clone();
            let usage_slot: Arc<Mutex<Option<UsageStats>>> = Arc::new(Mutex::new(None));
            let usage_writer = usage_slot.clone();
            std::thread::spawn(move || {
                let stats = UsageStats::load();
                *usage_writer.lock().unwrap() = Some(stats);
                usage_ctx.request_repaint();
            });
            index.refresh_boosts();

            Ok(Box::new(App {
                launcher: Launcher::new(index, Actions::resolve(), theme::dark_mode_now()),
                commands: command_receiver,
                pending_index: pending_for_app,
                pending_usage: usage_slot,
                focus_guard: None,
                visible: !as_daemon,
                as_daemon,
                chrome_applied: false,
                last_key_state: None,
                focus_settled: false,
                // In direct UI mode the window starts visible without going through `show`, so
                // the activation that grants keyboard focus has to be queued here instead.
                pending_front: !as_daemon,
                pending_out: false,
                last_height: initial_height,
            }))
        }),
    )
    .map_err(|error| anyhow::anyhow!("{error}"))
}

/// The daemon outside macOS.
///
/// winit cannot hide or re-show a window on Wayland, and eframe does not reliably return from
/// `run_native` there once its window is closed, so a resident hidden window does not work. Instead
/// each `show` runs the window in its own `ps_ui ui --entries-stdin` process. The entries are
/// loaded here once, at startup and on reload, and piped to it: opening a window never runs Python.
fn window_daemon() -> Result<()> {
    let mut entries = Actions::resolve().load_entries_json()?;

    let (command_sender, commands) = channel::<Command>();
    daemon::listen(command_sender, || {})?;

    let exe = std::env::current_exe()?;
    let mut window: Option<Child> = None;

    for command in commands {
        // A window closed with Esc has exited on its own; forget it so the next show opens one.
        if let Some(child) = &mut window {
            if !matches!(child.try_wait(), Ok(None)) {
                window = None;
            }
        }

        match window_action(command, window.is_some()) {
            WindowAction::Open => {
                if let Some(child) = window.take() {
                    close_window(child);
                }
                window = spawn_window(&exe, &entries);
            }
            WindowAction::Close => {
                if let Some(child) = window.take() {
                    close_window(child);
                }
            }
            WindowAction::Reload => match Actions::resolve().load_entries_json() {
                Ok(fresh) => entries = fresh,
                Err(error) => eprintln!("reload failed: {error}"),
            },
            WindowAction::Exit => {
                if let Some(child) = window.take() {
                    close_window(child);
                }
                return Ok(());
            }
            WindowAction::Nothing => {}
        }
    }
    Ok(())
}

/// What `window_daemon` does in response to a command.
#[derive(Debug, PartialEq, Eq)]
enum WindowAction {
    /// Open a window, replacing one that is already open.
    Open,
    Close,
    Reload,
    Exit,
    Nothing,
}

fn window_action(command: Command, window_open: bool) -> WindowAction {
    match command {
        // A window still running may have lost focus and sit behind others, and Wayland does not
        // let it raise itself. So show always opens a new one, which comes up on top, focused.
        Command::Show => WindowAction::Open,
        Command::Toggle if window_open => WindowAction::Close,
        Command::Toggle => WindowAction::Open,
        Command::Hide if window_open => WindowAction::Close,
        Command::Hide => WindowAction::Nothing,
        Command::Reload => WindowAction::Reload,
        Command::Quit => WindowAction::Exit,
        // The framebuffer capture belongs to the window process, which the daemon does not reach.
        Command::Screenshot => WindowAction::Nothing,
    }
}

fn spawn_window(exe: &std::path::Path, entries: &[u8]) -> Option<Child> {
    let spawned = std::process::Command::new(exe)
        .args(["ui", "--entries-stdin"])
        .stdin(Stdio::piped())
        .spawn();
    let mut child = match spawned {
        Ok(child) => child,
        Err(error) => {
            eprintln!("could not open the launcher window: {error}");
            return None;
        }
    };
    // Dropping the pipe after writing closes it, which ends the child's read.
    if let Some(mut stdin) = child.stdin.take() {
        if let Err(error) = stdin.write_all(entries) {
            eprintln!("could not send entries to the launcher window: {error}");
        }
    }
    Some(child)
}

fn close_window(mut child: Child) {
    let _ = child.kill();
    let _ = child.wait();
}

/// Reload the entries from Python, off the UI thread.
///
/// Loading costs ~150 ms of Python, so doing it inline would freeze the window — including the
/// spinner that is supposed to show it is working.
fn reload_in_background(
    pending: Arc<Mutex<Option<Index>>>,
    ctx: egui::Context,
) {
    std::thread::spawn(move || {
        match load_index() {
            Ok(fresh) => {
                *pending.lock().unwrap() = Some(fresh);
                if NOTIFY_DAEMON_ON_RELOAD.load(std::sync::atomic::Ordering::Relaxed) {
                    let _ = daemon::send(Command::Reload);
                }
            }
            Err(error) => eprintln!("reload failed: {error}"),
        }
        ctx.request_repaint();
    });
}

struct App {
    launcher: Launcher,
    commands: Receiver<Command>,
    pending_index: Arc<Mutex<Option<Index>>>,
    pending_usage: Arc<Mutex<Option<UsageStats>>>,
    focus_guard: Option<ps_mac::FocusGuard>,
    visible: bool,
    as_daemon: bool,
    chrome_applied: bool,
    last_key_state: Option<bool>,
    /// False between issuing a show and the panel actually becoming key.
    ///
    /// Activation is dispatched to the main queue, so for the first frames after a show the window
    /// is not key yet. Without this the panel would paint its unfocused (grey) styling on open and
    /// immediately drop its window level, fighting the activation still in flight.
    focus_settled: bool,
    /// Set by `show`, consumed in `ui` once the window handle is reachable. Taking key focus needs
    /// AppKit; eframe's `ViewportCommand::Focus` alone does not make an accessory-policy app key.
    pending_front: bool,
    pending_out: bool,
    /// Last height pushed to the window. Re-sending it every frame makes the resize echo back as a
    /// new frame, which spins the event loop at full tilt for no visual change.
    last_height: f32,
}

impl App {
    fn show(&mut self, ctx: &egui::Context) {
        if std::env::var("PS_DEBUG").is_ok() {
            eprintln!("show() called, visible was {}", self.visible);
        }
        // Deliberately no early return when already visible. The panel can be on screen without
        // being focused — the user clicked elsewhere, or another app stole activation — and in that
        // state the hotkey has to bring it back rather than do nothing. This mirrors the old
        // `focus_or_open` behaviour.
        if !self.visible {
            // Only capture the focus target when coming from hidden, so repeated shows do not
            // record the panel itself as the app to return to.
            self.focus_guard = Some(ps_mac::FocusGuard::capture());
        }
        self.launcher.reset();
        self.visible = true;
        // Force a reposition on the next frame: the panel follows the mouse's screen.
        self.last_height = 0.0;
        self.pending_front = true;
        self.pending_out = false;
        ctx.send_viewport_cmd(egui::ViewportCommand::Visible(true));
        // `order_front` is AppKit only; elsewhere ask the compositor to focus the window.
        #[cfg(not(target_os = "macos"))]
        ctx.send_viewport_cmd(egui::ViewportCommand::Focus);
        ctx.request_repaint();
    }

    fn hide(&mut self, ctx: &egui::Context) {
        if std::env::var("PS_DEBUG").is_ok() {
            eprintln!("hide() called, visible was {}", self.visible);
        }
        if !self.visible {
            return;
        }
        self.visible = false;
        self.pending_front = false;
        self.pending_out = true;
        ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false));
        ctx.request_repaint();
    }

    fn drain_commands(&mut self, ctx: &egui::Context) {
        while let Ok(command) = self.commands.try_recv() {
            match command {
                Command::Show => self.show(ctx),
                Command::Hide => self.hide(ctx),
                Command::Toggle => {
                    if self.visible {
                        self.hide(ctx);
                    } else {
                        self.show(ctx);
                    }
                }
                Command::Reload => {
                    self.launcher.set_reloading(true);
                    reload_in_background(self.pending_index.clone(), ctx.clone());
                }
                Command::Quit => std::process::exit(0),
                Command::Screenshot => {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Screenshot(
                        egui::UserData::default(),
                    ));
                    ctx.request_repaint();
                }
            }
        }
    }

    fn apply_pending(&mut self, ctx: &egui::Context) {
        if let Some(fresh) = self.pending_index.lock().unwrap().take() {
            let count = fresh.len();
            self.launcher.replace_index(fresh);
            self.launcher.index_mut().refresh_boosts();
            let now = ctx.input(|i| i.time);
            self.launcher
                .show_toast(format!("Reloaded {count} entries"), now);
        }
        if let Some(mut usage) = self.pending_usage.lock().unwrap().take() {
            self.launcher.set_query_history(usage.take_recent_queries());
            self.launcher.index_mut().set_usage(usage);
        }
    }
}

impl eframe::App for App {
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        // Fully transparent so the window's vibrancy layer shows through.
        [0.0, 0.0, 0.0, 0.0]
    }

    /// All window manipulation lives here rather than in `ui`.
    ///
    /// eframe runs no egui pass while the window is hidden — it calls `logic` instead — so any
    /// show/hide work driven from `ui` would never run once the panel was hidden, leaving it stuck
    /// on screen. `logic` is also outside the egui pass, which is where AppKit calls belong.
    fn logic(&mut self, ctx: &egui::Context, frame: &mut eframe::Frame) {
        // Closed from outside (window manager, Alt+F4): exit for the same reason as on Esc.
        if !self.as_daemon && ctx.input(|i| i.viewport().close_requested()) {
            std::process::exit(0);
        }
        self.drain_commands(ctx);
        self.apply_pending(ctx);

        let Ok(handle) = frame.window_handle() else {
            return;
        };
        let handle = handle.as_raw();

        if !self.chrome_applied {
            ps_mac::apply_panel_chrome(handle, Metrics::CORNER_RADIUS as f64);
            self.chrome_applied = true;
        }

        if self.pending_out {
            self.pending_out = false;
            ps_mac::order_out(handle);
            // Hand focus back only after the panel is off screen, otherwise macOS bounces it back.
            if let Some(guard) = self.focus_guard.take() {
                guard.restore();
            }
        }

        if self.pending_front {
            self.pending_front = false;
            ps_mac::order_front(handle);
        }

        if self.visible {
            #[cfg(target_os = "macos")]
            let is_key = ps_mac::is_key_window(handle);
            // The AppKit query has no equivalent elsewhere; egui tracks focus from winit events.
            #[cfg(not(target_os = "macos"))]
            let is_key = ctx.input(|i| i.viewport().focused.unwrap_or(true));

            if !self.focus_settled {
                // Still waiting for the activation to take effect. Keep rendering as focused, and
                // do not touch the window level, until the panel really is key.
                if is_key {
                    self.focus_settled = true;
                } else {
                    ctx.request_repaint();
                    return;
                }
            }

            self.launcher.set_focused(is_key);
            if self.last_key_state != Some(is_key) {
                self.last_key_state = Some(is_key);
                // Only stay above other windows while focused. Clicking another window should put
                // the panel behind it rather than leave it obstructing whatever the user moved to.
                ps_mac::set_floating(handle, is_key);
                ctx.request_repaint();
                if std::env::var("PS_DEBUG").is_ok() {
                    eprintln!("key status changed: isKey={is_key}");
                }
            }
        }
    }

    fn ui(&mut self, ui: &mut egui::Ui, frame: &mut eframe::Frame) {
        let ctx = ui.ctx().clone();

        // Deliver any framebuffer capture requested through `ps_ui screenshot`.
        let shots: Vec<_> = ctx.input(|i| {
            i.events
                .iter()
                .filter_map(|event| match event {
                    egui::Event::Screenshot { image, .. } => Some(image.clone()),
                    _ => None,
                })
                .collect()
        });
        for shot in shots {
            save_screenshot(&shot);
        }

        if !self.visible {
            return;
        }

        // An idle window gets no frames, so a focus change elsewhere would leave the styling
        // stale. Four ticks a second is enough to keep it honest and costs nothing measurable.
        ctx.request_repaint_after(std::time::Duration::from_millis(250));

        self.launcher.set_dark_mode(theme::dark_mode_now());

        let outcome = self.launcher.ui(ui);

        if self.launcher.reload_requested {
            self.launcher.reload_requested = false;
            self.launcher.set_reloading(true);
            reload_in_background(self.pending_index.clone(), ctx.clone());
        }

        // Grow and shrink with the result list, then re-centre so the panel stays put visually.
        let height = self.launcher.desired_height();
        if (height - self.last_height).abs() > 0.5 {
            self.last_height = height;
            ctx.send_viewport_cmd(egui::ViewportCommand::InnerSize(egui::vec2(
                Metrics::WINDOW_WIDTH,
                height,
            )));
            if let Ok(handle) = frame.window_handle() {
                ps_mac::center_on_active_screen(
                    handle.as_raw(),
                    Metrics::WINDOW_WIDTH as f64,
                    height as f64,
                );
            }
        }

        if let Outcome::Hide = outcome {
            if self.as_daemon {
                self.hide(&ctx);
            } else {
                // Exit rather than close: on Wayland eframe does not reliably return from a closed
                // window, and a lingering process would look like an open launcher to the daemon.
                std::process::exit(0);
            }
        }
    }
}

fn search(query: &str) -> Result<()> {
    let started = std::time::Instant::now();
    let mut index = load_index()?;
    let loaded = started.elapsed();

    let usage_started = std::time::Instant::now();
    index.set_usage(UsageStats::load());
    let usage_loaded = usage_started.elapsed();

    let search_started = std::time::Instant::now();
    let matches = index.search(query);
    let searched = search_started.elapsed();

    for m in matches.iter().take(10) {
        let entry = index.entry(m.index);
        println!(
            "{:>8.1}  [{:<4}] {:<50} {}",
            m.score,
            entry.entry_type.label(),
            truncate(&entry.key, 50),
            truncate(entry.display_content(), 60)
        );
    }

    eprintln!(
        "\n{} entries | load {:.1?} | usage {:.1?} | search {:.3?} | {} matches",
        index.len(),
        loaded,
        usage_loaded,
        searched,
        matches.len()
    );
    Ok(())
}

fn truncate(value: &str, width: usize) -> String {
    if value.chars().count() <= width {
        return value.to_string();
    }
    let kept: String = value.chars().take(width.saturating_sub(1)).collect();
    format!("{kept}…")
}

/// Write a captured framebuffer to `~/.python_search/screenshot.png`.
fn save_screenshot(image: &egui::ColorImage) {
    let path = dirs::home_dir()
        .map(|home| home.join(".python_search/screenshot.png"))
        .unwrap_or_else(|| std::path::PathBuf::from("screenshot.png"));

    let width = image.width() as u32;
    let height = image.height() as u32;
    let mut buffer = Vec::with_capacity((width * height * 4) as usize);
    for pixel in &image.pixels {
        let [r, g, b, a] = pixel.to_array();
        buffer.extend_from_slice(&[r, g, b, a]);
    }

    match image::RgbaImage::from_raw(width, height, buffer) {
        Some(rgba) => match rgba.save(&path) {
            Ok(()) => eprintln!("screenshot written to {}", path.display()),
            Err(error) => eprintln!("could not write screenshot: {error}"),
        },
        None => eprintln!("screenshot buffer had unexpected size"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn show_always_opens_a_new_window() {
        assert_eq!(window_action(Command::Show, false), WindowAction::Open);
        assert_eq!(window_action(Command::Show, true), WindowAction::Open);
    }

    #[test]
    fn toggle_closes_an_open_window_and_opens_otherwise() {
        assert_eq!(window_action(Command::Toggle, true), WindowAction::Close);
        assert_eq!(window_action(Command::Toggle, false), WindowAction::Open);
    }

    #[test]
    fn hide_only_acts_on_an_open_window() {
        assert_eq!(window_action(Command::Hide, true), WindowAction::Close);
        assert_eq!(window_action(Command::Hide, false), WindowAction::Nothing);
    }

    #[test]
    fn reload_quit_and_screenshot_do_not_depend_on_the_window() {
        for open in [true, false] {
            assert_eq!(window_action(Command::Reload, open), WindowAction::Reload);
            assert_eq!(window_action(Command::Quit, open), WindowAction::Exit);
            assert_eq!(window_action(Command::Screenshot, open), WindowAction::Nothing);
        }
    }
}
