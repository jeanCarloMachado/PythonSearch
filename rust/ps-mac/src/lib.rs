//! Native macOS window behaviour for the launcher.
//!
//! eframe gives us a `winit` window, which is enough to draw into but not enough to *behave* like
//! Spotlight. Everything here is the AppKit layer on top: vibrancy, window level, Space behaviour,
//! placement, and returning keyboard focus to whatever the user was doing before.

#[cfg(target_os = "macos")]
mod imp;

#[cfg(target_os = "macos")]
pub use imp::*;

#[cfg(not(target_os = "macos"))]
mod stub {
    use raw_window_handle::RawWindowHandle;

    pub struct FocusGuard;

    impl FocusGuard {
        pub fn capture() -> Self {
            FocusGuard
        }
        pub fn restore(&self) {}
    }

    pub fn apply_panel_chrome(_handle: RawWindowHandle, _corner_radius: f64) {}
    pub fn hide_from_dock() {}
    pub fn center_on_active_screen(_handle: RawWindowHandle, _width: f64, _height: f64) {}
    pub fn center_on_main_screen(_handle: RawWindowHandle, _width: f64, _height: f64) {}
    /// Follows GNOME's `color-scheme` setting; dark when it cannot be read.
    pub fn is_dark_mode() -> bool {
        std::process::Command::new("gsettings")
            .args(["get", "org.gnome.desktop.interface", "color-scheme"])
            .output()
            .map(|output| {
                let scheme = String::from_utf8_lossy(&output.stdout);
                !output.status.success() || scheme.contains("dark")
            })
            .unwrap_or(true)
    }
    pub fn local_hour() -> u8 {
        let mut tm: libc::tm = unsafe { std::mem::zeroed() };
        let now = unsafe { libc::time(std::ptr::null_mut()) };
        if unsafe { libc::localtime_r(&now, &mut tm) }.is_null() {
            return 12;
        }
        tm.tm_hour.clamp(0, 23) as u8
    }
    pub fn set_floating(_handle: RawWindowHandle, _floating: bool) {}
    pub fn set_movable(_handle: RawWindowHandle, _movable: bool) {}
    pub fn order_out(_handle: RawWindowHandle) {}
    pub fn order_front(_handle: RawWindowHandle) {}
    pub fn is_key_window(_handle: RawWindowHandle) -> bool {
        false
    }
}

#[cfg(not(target_os = "macos"))]
pub use stub::*;

#[cfg(all(test, not(target_os = "macos")))]
mod tests {
    #[test]
    fn local_hour_matches_the_system_clock() {
        let expected = std::process::Command::new("date")
            .arg("+%H")
            .output()
            .map(|output| String::from_utf8_lossy(&output.stdout).trim().parse::<u8>().unwrap())
            .unwrap();
        // Tolerate the hour rolling over between the two reads.
        let hour = super::local_hour();
        assert!(hour == expected || hour == (expected + 1) % 24, "{hour} vs {expected}");
    }
}
