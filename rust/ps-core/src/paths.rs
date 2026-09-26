use std::path::PathBuf;

/// Root of PythonSearch's on-disk state. Mirrors `python_search/configuration/data_config.py`.
pub fn data_dir() -> PathBuf {
    dirs::home_dir()
        .expect("no home directory")
        .join(".python_search/data")
}

/// The rich entries dump written by `python_search _entries_loader dump_entries`.
pub fn entries_dump() -> PathBuf {
    data_dir().join("entries.json")
}

pub fn entries_dump_meta() -> PathBuf {
    data_dir().join("entries.json.meta")
}

/// One JSON file per executed entry, written by both the Python side and this launcher.
pub fn searches_performed_dir() -> PathBuf {
    data_dir().join("searches_performed")
}

/// Socket the resident daemon listens on.
pub fn daemon_socket() -> PathBuf {
    dirs::home_dir()
        .expect("no home directory")
        .join(".python_search/ps.sock")
}

/// Directory holding the installed PythonSearch console scripts (`run_key`, `entries_editor`, ...).
///
/// `python_search/host_system/system_paths.py` resolves these as `dirname(sys.executable)/<name>`,
/// which on this machine is a conda env bin dir that a LaunchAgent does not inherit on PATH.
/// Resolved once at daemon start, never on the search path.
pub fn resolve_binaries_dir() -> Option<PathBuf> {
    if let Ok(dir) = std::env::var("PS_BIN_PATH") {
        let dir = PathBuf::from(dir);
        if dir.join("run_key").exists() {
            return Some(dir);
        }
    }

    // `~/.local/bin` is searched too, since a desktop-launched daemon may not have it on PATH.
    let mut dirs: Vec<PathBuf> = std::env::var_os("PATH")
        .map(|path| std::env::split_paths(&path).collect())
        .unwrap_or_default();
    if let Some(home) = dirs::home_dir() {
        dirs.push(home.join(".local/bin"));
    }
    for dir in dirs {
        if dir.join("run_key").exists() {
            return Some(dir);
        }
        // Only `python_search` may be linked onto PATH; the other scripts sit next to its target.
        if let Some(target_dir) = std::fs::canonicalize(dir.join("python_search"))
            .ok()
            .and_then(|target| target.parent().map(PathBuf::from))
        {
            if target_dir.join("run_key").exists() {
                return Some(target_dir);
            }
        }
    }

    // Last resort: ask a login shell, which has the user's full environment.
    let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/sh".to_string());
    let output = std::process::Command::new(shell)
        .args(["-lc", "command -v run_key"])
        .output()
        .ok()?;
    let found = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if found.is_empty() {
        return None;
    }
    PathBuf::from(found).parent().map(PathBuf::from)
}
