//! Bakes the git commit and build time into the binary, shown in the launcher's hint row so it is
//! obvious which build the running daemon is.

use std::process::Command;

fn output(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd)
        .args(args)
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_else(|| "unknown".to_string())
}

fn main() {
    let sha = output("git", &["rev-parse", "--short=7", "HEAD"]);
    let built_at = output("date", &["+%Y-%m-%d %H:%M"]);
    println!("cargo:rustc-env=PS_UI_GIT_SHA={sha}");
    println!("cargo:rustc-env=PS_UI_BUILT_AT={built_at}");

    // Re-run when the commit or working tree changes, or when the launcher's sources do.
    let git_dir = output("git", &["rev-parse", "--absolute-git-dir"]);
    for path in ["HEAD", "index"] {
        println!("cargo:rerun-if-changed={git_dir}/{path}");
    }
    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=../ps-core/src");
}
