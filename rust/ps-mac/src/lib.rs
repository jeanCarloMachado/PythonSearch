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
    pub fn is_dark_mode() -> bool {
        true
    }
    pub fn local_hour() -> u8 {
        12
    }
    pub fn set_floating(_handle: RawWindowHandle, _floating: bool) {}
    pub fn order_out(_handle: RawWindowHandle) {}
    pub fn order_front(_handle: RawWindowHandle) {}
    pub fn is_key_window(_handle: RawWindowHandle) -> bool {
        false
    }
}

#[cfg(not(target_os = "macos"))]
pub use stub::*;
