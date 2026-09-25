use crate::paths;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

/// The entry the terminal UI's `?` shortcut runs; it googles whatever is on the clipboard.
const GOOGLE_SEARCH_ENTRY: &str = "search in google using clipboard content";

/// Dispatches entry actions by invoking the installed PythonSearch console scripts.
///
/// This is deliberately the same boundary as `search_ui/search_actions.py`: every interpreter
/// behaviour (`call_before`, `call_after`, `app_mode`, `focus_match`, `callable`) stays in Python,
/// so the launcher cannot drift from what `term_ui` does. All spawns are fire and forget.
#[derive(Clone)]
pub struct Actions {
    bin_dir: Option<PathBuf>,
}

impl Actions {
    pub fn resolve() -> Self {
        Actions {
            bin_dir: paths::resolve_binaries_dir(),
        }
    }

    /// Point at an explicit binaries directory instead of resolving one from the environment.
    /// Exists for tests, which stand in a fake `python_search` rather than touching the real one.
    pub fn with_bin_dir(bin_dir: PathBuf) -> Self {
        Actions {
            bin_dir: Some(bin_dir),
        }
    }

    fn binary(&self, name: &str) -> PathBuf {
        match &self.bin_dir {
            Some(dir) => dir.join(name),
            None => PathBuf::from(name),
        }
    }

    fn spawn(&self, name: &str, args: &[&str]) {
        let binary = self.binary(name);
        let result = Command::new(&binary)
            .args(args)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();

        if let Err(error) = result {
            eprintln!("failed to spawn {}: {error}", binary.display());
        }
    }

    /// Execute the entry. Equivalent to `Actions.run_key` in the Python UI.
    pub fn run_key(&self, key: &str) {
        self.spawn("run_key", &[key]);
    }

    /// Open the entry's definition in the editor. Equivalent to `Actions.edit_key`.
    pub fn edit_key(&self, key: &str) {
        self.spawn("entries_editor", &["edit_key", key]);
    }

    /// LLM assisted deletion. Equivalent to `Actions.delete_key`.
    pub fn delete_key(&self, key: &str) {
        self.spawn("entries_editor", &["delete_key", key]);
    }

    /// Copy the entry's value to the clipboard. Equivalent to `Actions.copy_entry_value_to_clipboard`.
    pub fn copy_value(&self, key: &str) {
        self.spawn("share_entry", &["share_only_value", key]);
    }

    /// Google the current query, mirroring `Actions.search_in_google` in the terminal UI (bound
    /// to `?` there).
    ///
    /// The clipboard has to be set *before* the entry runs, since the entry reads from it. The two
    /// steps run on a background thread rather than through a shell `&&`, which keeps the query
    /// out of a shell command line entirely — no quoting to get wrong, whatever the user typed.
    pub fn search_in_google(&self, query: &str) {
        let clipboard = self.binary("clipboard");
        let run_key = self.binary("run_key");
        let query = query.to_string();

        std::thread::spawn(move || {
            let staged = Command::new(&clipboard)
                .arg("set_content")
                .arg(&query)
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();

            match staged {
                Ok(status) if status.success() => {}
                Ok(status) => {
                    eprintln!("clipboard set_content exited with {status}");
                    return;
                }
                Err(error) => {
                    eprintln!("could not set the clipboard: {error}");
                    return;
                }
            }

            let _ = Command::new(&run_key)
                .arg(GOOGLE_SEARCH_ENTRY)
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn();
        });
    }

    /// Register a new entry. Equivalent to `RegisterNew.register` in Python, invoked through the
    /// `python_search register_new` console script so the insertion logic stays in one place.
    ///
    /// Unlike the other actions here this waits for the process and reports failure, rather than
    /// firing and forgetting: it is a one-shot, user-initiated write, not a background side effect,
    /// so a bad key or a binary-resolution problem should surface instead of silently doing nothing.
    pub fn register_new(&self, key: &str, value: &str, entry_type: &str) -> Result<(), String> {
        let binary = self.binary("python_search");
        let output = Command::new(&binary)
            .args(["register_new", key, value, "--type", entry_type])
            .stdin(Stdio::null())
            .output()
            .map_err(|error| format!("failed to run {}: {error}", binary.display()))?;

        if output.status.success() {
            Ok(())
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            let message = stderr.lines().last().unwrap_or("unknown error");
            Err(message.to_string())
        }
    }

    /// Regenerate the entries dump. Runs in the background; the watcher picks up the new file.
    pub fn dump_entries(&self) -> std::io::Result<std::process::Child> {
        Command::new(self.binary("python_search"))
            .args(["_entries_loader", "dump_entries"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
    }
}

/// Append a run event in the same shape `python_search/events/run_performed/` writes, so the Python
/// side and the launcher share one history and the usage boost sees runs from both.
pub fn log_run(key: &str, query: &str) -> f64 {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0);

    let dir = paths::searches_performed_dir();
    if std::fs::create_dir_all(&dir).is_err() {
        return timestamp;
    }

    let record = serde_json::json!({
        "key": key,
        "query_input": query,
        "shortcut": false,
        "timestamp": format!("{timestamp:.6}"),
        "rank_uuid": null,
        "rank_position": null,
    });

    let path = dir.join(format!("{timestamp:.6}.json"));
    let _ = std::fs::write(path, record.to_string());
    timestamp
}

#[cfg(test)]
mod tests {
    use super::Actions;
    use std::io::Write;
    use std::os::unix::fs::PermissionsExt;

    /// A directory holding a fake `python_search` script, so tests exercise the real subprocess
    /// plumbing (arg order, exit status, stderr capture) without touching the real installation or
    /// writing to the user's actual entries.
    struct FakeBinDir {
        dir: std::path::PathBuf,
    }

    impl FakeBinDir {
        /// `body` is a POSIX shell script body; `$1 $2 ...` are `python_search`'s own arguments.
        fn new(body: &str) -> Self {
            let dir = std::env::temp_dir().join(format!(
                "ps-core-actions-test-{}-{:?}",
                std::process::id(),
                std::thread::current().id()
            ));
            std::fs::create_dir_all(&dir).unwrap();

            let script_path = dir.join("python_search");
            let mut script = std::fs::File::create(&script_path).unwrap();
            writeln!(script, "#!/bin/sh").unwrap();
            writeln!(script, "{body}").unwrap();
            drop(script);
            std::fs::set_permissions(&script_path, std::fs::Permissions::from_mode(0o755))
                .unwrap();

            FakeBinDir { dir }
        }

        fn actions(&self) -> Actions {
            Actions::with_bin_dir(self.dir.clone())
        }
    }

    impl Drop for FakeBinDir {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.dir);
        }
    }

    #[test]
    fn register_new_ok_on_successful_exit() {
        let fake = FakeBinDir::new("exit 0");
        let result = fake.actions().register_new("a key", "a value", "snippet");
        assert_eq!(result, Ok(()));
    }

    #[test]
    fn register_new_reports_stderr_on_failure() {
        let fake = FakeBinDir::new("echo 'Exception: Key is required' >&2; exit 1");
        let result = fake.actions().register_new("", "a value", "snippet");
        assert_eq!(result, Err("Exception: Key is required".to_string()));
    }

    #[test]
    fn register_new_passes_key_value_and_type_positionally() {
        // Echoes the arguments it actually received back on stdout via stderr (so a *failing* exit
        // gets them into the `Err` message this test asserts on), proving the call shape matches
        // what `python_search register_new KEY VALUE --type TYPE` expects.
        let fake = FakeBinDir::new(r#"echo "$1|$2|$3|$4|$5" >&2; exit 1"#);
        let result = fake.actions().register_new("my key", "my value", "url");
        assert_eq!(
            result,
            Err("register_new|my key|my value|--type|url".to_string())
        );
    }

    #[test]
    fn register_new_errors_when_binary_is_missing() {
        let fake = FakeBinDir::new("exit 0");
        std::fs::remove_file(fake.dir.join("python_search")).unwrap();

        let result = fake.actions().register_new("a key", "a value", "snippet");
        assert!(result.is_err());
    }
}
