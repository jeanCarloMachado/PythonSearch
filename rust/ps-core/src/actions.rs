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
pub struct Actions {
    bin_dir: Option<PathBuf>,
}

impl Actions {
    pub fn resolve() -> Self {
        Actions {
            bin_dir: paths::resolve_binaries_dir(),
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
