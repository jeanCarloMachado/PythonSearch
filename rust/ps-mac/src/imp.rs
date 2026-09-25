use objc2::rc::Retained;
use objc2::runtime::AnyObject;
use objc2::{msg_send, MainThreadMarker, MainThreadOnly};
use objc2_app_kit::{
    NSApplication, NSApplicationActivationPolicy, NSColor, NSRunningApplication, NSScreen, NSView,
    NSVisualEffectBlendingMode, NSVisualEffectMaterial, NSVisualEffectState, NSVisualEffectView,
    NSWindow, NSWindowCollectionBehavior, NSWindowStyleMask,
};
use objc2_foundation::{NSPoint, NSRect, NSSize};
use raw_window_handle::RawWindowHandle;

/// Window level constant for `NSFloatingWindowLevel`. Not exposed as a named constant by the
/// bindings, and this is the level Spotlight-class panels sit at: above normal windows, below
/// system alerts.
const FLOATING_WINDOW_LEVEL: isize = 3;

/// `NSNormalWindowLevel`: an ordinary window, which other windows can cover.
const NORMAL_WINDOW_LEVEL: isize = 0;

/// Vertical position of the panel as a fraction of screen height, measured from the top.
/// Spotlight sits noticeably above centre; dead centre reads as a modal dialog.
const VERTICAL_POSITION: f64 = 0.22;

/// Run `work` on the main queue, after the current event finishes.
///
/// winit holds a `RefCell` borrow on its view while dispatching an event, and every call here
/// arrives from inside an egui frame. Mutating the window or its view hierarchy synchronously
/// re-enters that borrow and panics with "RefCell already borrowed", so the work is always
/// deferred by one turn of the run loop.
fn on_main_queue(work: impl FnOnce() + Send + 'static) {
    dispatch2::DispatchQueue::main().exec_async(work);
}

/// Run `work` on the main queue after `delay`.
fn on_main_queue_after(delay: std::time::Duration, work: impl FnOnce() + Send + 'static) {
    let when = dispatch2::DispatchTime::NOW.time(delay.as_nanos() as i64);
    let _ = dispatch2::DispatchQueue::main().after(when, work);
}

/// A window handle is only valid on the thread that owns it; this wrapper carries the pointer
/// across the `exec_async` boundary, which is sound because the closure runs on the main thread.
#[derive(Clone, Copy)]
struct MainThreadHandle(RawWindowHandle);

unsafe impl Send for MainThreadHandle {}

impl MainThreadHandle {
    /// Taking `self` forces the closure to capture the whole wrapper rather than the inner
    /// handle, which is what makes the closure `Send`.
    fn get(self) -> RawWindowHandle {
        self.0
    }
}

fn window_from_handle(handle: RawWindowHandle) -> Option<Retained<NSWindow>> {
    let RawWindowHandle::AppKit(handle) = handle else {
        return None;
    };
    // `ns_view` is the content view; its `window` is what we need to configure.
    let view: &NSView = unsafe { &*(handle.ns_view.as_ptr() as *const NSView) };
    view.window()
}

/// Make the window look and behave like a system panel rather than an application window.
pub fn apply_panel_chrome(handle: RawWindowHandle, corner_radius: f64) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || apply_panel_chrome_now(handle.get(), corner_radius));
}

fn apply_panel_chrome_now(handle: RawWindowHandle, corner_radius: f64) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };

    unsafe {
        // A titled window with a hidden titlebar, rather than a borderless one. Borderless
        // windows return NO from `canBecomeKeyWindow`, so the panel would draw but never take
        // keyboard focus.
        window.setStyleMask(
            NSWindowStyleMask::Titled
                | NSWindowStyleMask::FullSizeContentView
                | NSWindowStyleMask::Borderless,
        );
        window.setTitlebarAppearsTransparent(true);
        window.setTitleVisibility(objc2_app_kit::NSWindowTitleVisibility::Hidden);
        window.setMovable(false);
        window.setOpaque(false);
        window.setBackgroundColor(Some(&NSColor::clearColor()));
        // The shadow belongs to the backdrop window, which is the opaque one.
        window.setHasShadow(false);
        window.setLevel(FLOATING_WINDOW_LEVEL);

        for button in [
            objc2_app_kit::NSWindowButton::CloseButton,
            objc2_app_kit::NSWindowButton::MiniaturizeButton,
            objc2_app_kit::NSWindowButton::ZoomButton,
        ] {
            if let Some(button) = window.standardWindowButton(button) {
                button.setHidden(true);
            }
        }

        // Appear on whichever Space is active, including over fullscreen apps, and do not get
        // dragged along by Mission Control as a regular window would.
        window.setCollectionBehavior(
            NSWindowCollectionBehavior::CanJoinAllSpaces
                | NSWindowCollectionBehavior::FullScreenAuxiliary
                | NSWindowCollectionBehavior::Stationary,
        );
    }

    // Round the render surface itself. Only layer properties are touched here: re-parenting the
    // view is what panics winit, not configuring it.
    if let Some(view) = window.contentView() {
        view.setWantsLayer(true);
        unsafe {
            let layer: *mut AnyObject = msg_send![&*view, layer];
            if !layer.is_null() {
                let _: () = msg_send![layer, setCornerRadius: corner_radius];
                let _: () = msg_send![layer, setMasksToBounds: true];
            }
        }
    }

    // `setStyleMask` rebuilds the window's frame view, which can leave the first responder nil.
    // The window is then key — it looks focused — but key events have nowhere to go. Pointing the
    // responder back at the render view is what actually makes typing arrive.
    if let Some(view) = window.contentView() {
        window.makeFirstResponder(Some(&view));
        if std::env::var("PS_DEBUG").is_ok() {
            eprintln!(
                "first responder set: {}",
                window.firstResponder().is_some()
            );
        }
    }

    attach_backdrop(&window, corner_radius);
}

/// The vibrancy backdrop lives in its own borderless child window sitting directly behind the
/// panel, rather than as a view inside it.
///
/// The obvious approach — making an `NSVisualEffectView` the window's content view and reparenting
/// winit's view into it — cannot be used: winit's view *is* the Metal surface, and moving it makes
/// AppKit recompute cursor rects re-entrantly, which panics winit 0.30 with
/// "RefCell already borrowed" (`view.rs:871`). A child window gives the same visual result and
/// never touches winit's hierarchy.
fn attach_backdrop(window: &NSWindow, corner_radius: f64) {
    let Some(mtm) = MainThreadMarker::new() else {
        return;
    };

    if backdrop_window().is_some() {
        return;
    }

    unsafe {
        let backdrop = NSWindow::initWithContentRect_styleMask_backing_defer(
            NSWindow::alloc(mtm),
            window.frame(),
            NSWindowStyleMask::Borderless,
            objc2_app_kit::NSBackingStoreType::Buffered,
            false,
        );

        backdrop.setOpaque(false);
        backdrop.setBackgroundColor(Some(&NSColor::clearColor()));
        backdrop.setHasShadow(true);
        backdrop.setLevel(FLOATING_WINDOW_LEVEL);
        backdrop.setIgnoresMouseEvents(true);
        backdrop.setCollectionBehavior(
            NSWindowCollectionBehavior::CanJoinAllSpaces
                | NSWindowCollectionBehavior::FullScreenAuxiliary
                | NSWindowCollectionBehavior::Stationary,
        );

        let effect_view = NSVisualEffectView::new(mtm);
        effect_view.setMaterial(NSVisualEffectMaterial::HUDWindow);
        effect_view.setBlendingMode(NSVisualEffectBlendingMode::BehindWindow);
        effect_view.setState(NSVisualEffectState::Active);
        effect_view.setWantsLayer(true);

        let layer: *mut AnyObject = msg_send![&*effect_view, layer];
        if !layer.is_null() {
            let _: () = msg_send![layer, setCornerRadius: corner_radius];
            let _: () = msg_send![layer, setMasksToBounds: true];
        }

        backdrop.setContentView(Some(&effect_view));

        // Ordered Below keeps it pinned behind the panel and following it around.
        window.addChildWindow_ordered(&backdrop, objc2_app_kit::NSWindowOrderingMode::Below);

        set_backdrop_window(backdrop);
    }
}

thread_local! {
    /// Main thread only: every access happens inside `on_main_queue`.
    static BACKDROP: std::cell::RefCell<Option<Retained<NSWindow>>> =
        const { std::cell::RefCell::new(None) };
}

fn backdrop_window() -> Option<Retained<NSWindow>> {
    BACKDROP.with(|slot| slot.borrow().clone())
}

fn set_backdrop_window(window: Retained<NSWindow>) {
    BACKDROP.with(|slot| *slot.borrow_mut() = Some(window));
}

/// Run without a Dock icon or menu bar, like a system utility.
pub fn hide_from_dock() {
    let Some(mtm) = MainThreadMarker::new() else {
        return;
    };
    let app = NSApplication::sharedApplication(mtm);
    app.setActivationPolicy(NSApplicationActivationPolicy::Accessory);
}

/// Position the panel on the screen the mouse is on, horizontally centred and high on the screen.
pub fn center_on_active_screen(handle: RawWindowHandle, width: f64, height: f64) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || center_on_active_screen_now(handle.get(), width, height));
}

fn center_on_active_screen_now(handle: RawWindowHandle, width: f64, height: f64) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    let Some(mtm) = MainThreadMarker::new() else {
        return;
    };

    let mouse = objc2_app_kit::NSEvent::mouseLocation();
    let screen = NSScreen::screens(mtm)
        .iter()
        .find(|screen| {
            let frame = screen.frame();
            mouse.x >= frame.origin.x
                && mouse.x < frame.origin.x + frame.size.width
                && mouse.y >= frame.origin.y
                && mouse.y < frame.origin.y + frame.size.height
        })
        .or_else(|| NSScreen::mainScreen(mtm))
        .map(|screen| screen.visibleFrame());

    let Some(visible) = screen else {
        return;
    };

    let x = visible.origin.x + (visible.size.width - width) / 2.0;
    // AppKit's origin is bottom-left, so "22% from the top" counts down from the frame's top edge.
    let y = visible.origin.y + visible.size.height
        - (visible.size.height * VERTICAL_POSITION)
        - height;

    window.setFrame_display(
        NSRect::new(NSPoint::new(x, y), NSSize::new(width, height)),
        true,
    );

}

/// Position a window dead-centre on the primary screen, ignoring the mouse. Used by satellite
/// windows (e.g. the register-new form) that should always open in the same place rather than
/// trailing the pointer like the mouse-following launcher panel does.
pub fn center_on_main_screen(handle: RawWindowHandle, width: f64, height: f64) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || center_on_main_screen_now(handle.get(), width, height));
}

fn center_on_main_screen_now(handle: RawWindowHandle, width: f64, height: f64) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    let Some(mtm) = MainThreadMarker::new() else {
        return;
    };

    let Some(visible) = NSScreen::mainScreen(mtm).map(|screen| screen.visibleFrame()) else {
        return;
    };

    let x = visible.origin.x + (visible.size.width - width) / 2.0;
    let y = visible.origin.y + (visible.size.height - height) / 2.0;

    window.setFrame_display(
        NSRect::new(NSPoint::new(x, y), NSSize::new(width, height)),
        true,
    );
}

pub fn is_dark_mode() -> bool {
    let Some(mtm) = MainThreadMarker::new() else {
        return true;
    };
    let app = NSApplication::sharedApplication(mtm);
    app.effectiveAppearance().name().to_string().contains("Dark")
}

/// Show the panel and take keyboard focus, without the app becoming the "active" app in the
/// conventional sense.
/// How many times to re-attempt activation before giving up.
///
/// macOS can refuse the first activation request from an app that has not been active recently
/// ("cooperative activation"), which showed up as needing to press the hotkey twice. Re-checking
/// and retrying costs nothing when the first attempt worked.
const ACTIVATION_ATTEMPTS: u8 = 4;

pub fn order_front(handle: RawWindowHandle) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || order_front_now_with_retry(handle.get(), ACTIVATION_ATTEMPTS));
}

fn order_front_now_with_retry(handle: RawWindowHandle, attempts_left: u8) {
    order_front_now(handle);

    if attempts_left <= 1 {
        return;
    }

    let still_unfocused = window_from_handle(handle).is_some_and(|window| !window.isKeyWindow());
    if !still_unfocused {
        return;
    }

    let handle = MainThreadHandle(handle);
    on_main_queue_after(std::time::Duration::from_millis(40), move || {
        let handle = handle.get();
        // Stop as soon as it has taken focus, so a user clicking elsewhere is not fought over.
        if window_from_handle(handle).is_some_and(|window| window.isKeyWindow()) {
            return;
        }
        order_front_now_with_retry(handle, attempts_left - 1);
    });
}

fn order_front_now(handle: RawWindowHandle) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    let Some(mtm) = MainThreadMarker::new() else {
        return;
    };
    let app = NSApplication::sharedApplication(mtm);

    // Getting keyboard focus as an accessory-policy app is the awkward part. On recent macOS,
    // `activateIgnoringOtherApps:` is ignored, so the app never becomes active and the panel never
    // becomes key — it draws, but typing goes to whatever is behind it.
    //
    // Switching to the regular activation policy makes the app eligible to activate. Switching
    // straight back to accessory immediately *drops* that activation — the app is frontmost for a
    // few milliseconds and then focus returns to whatever was there before. So the policy stays
    // regular for as long as the panel is up, and `order_out` puts it back.
    app.setActivationPolicy(NSApplicationActivationPolicy::Regular);
    unsafe {
        let running = NSRunningApplication::currentApplication();
        running.activateWithOptions(
            objc2_app_kit::NSApplicationActivationOptions::ActivateIgnoringOtherApps
                | objc2_app_kit::NSApplicationActivationOptions::ActivateAllWindows,
        );
    }

    window.makeKeyAndOrderFront(None);

    window.setLevel(FLOATING_WINDOW_LEVEL);

    // Re-attach the backdrop, which `order_out` detached, and re-sync its frame: AppKit child
    // windows follow a parent that moves but not one that resizes.
    if let Some(backdrop) = backdrop_window() {
        backdrop.setFrame_display(window.frame(), true);
        backdrop.setLevel(FLOATING_WINDOW_LEVEL);
        unsafe {
            window.addChildWindow_ordered(&backdrop, objc2_app_kit::NSWindowOrderingMode::Below);
        }
    }

    if std::env::var("PS_DEBUG").is_ok() {
        eprintln!(
            "order_front: isKey={} isVisible={} isMain={} appActive={}",
            window.isKeyWindow(),
            window.isVisible(),
            window.isMainWindow(),
            NSApplication::sharedApplication(mtm).isActive(),
        );
    }
}

pub fn order_out(handle: RawWindowHandle) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || order_out_now(handle.get()));
}

fn order_out_now(handle: RawWindowHandle) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    // The backdrop is a child window, and ordering out the parent does not reliably take it with
    // it. Detach and hide it explicitly. It is re-attached on the next show: doing it here would
    // undo the hide, because adding a child window orders it — and its parent — back in.
    if let Some(backdrop) = backdrop_window() {
        window.removeChildWindow(&backdrop);
        backdrop.orderOut(None);
    }

    window.orderOut(None);

    // Back out of the Dock and the app switcher now that the panel is gone.
    if let Some(mtm) = MainThreadMarker::new() {
        NSApplication::sharedApplication(mtm)
            .setActivationPolicy(NSApplicationActivationPolicy::Accessory);
    }
}

/// Remembers which application was frontmost so focus can be handed back on hide.
///
/// Without this, dismissing the launcher leaves the user in no particular app and their next
/// keystroke goes nowhere useful.
pub struct FocusGuard {
    previous: Option<Retained<NSRunningApplication>>,
}

impl FocusGuard {
    pub fn capture() -> Self {
        let previous = objc2_app_kit::NSWorkspace::sharedWorkspace().frontmostApplication();
        FocusGuard { previous }
    }

    pub fn restore(&self) {
        let Some(app) = &self.previous else {
            return;
        };
        app.activateWithOptions(objc2_app_kit::NSApplicationActivationOptions::empty());
    }
}

/// Whether the panel currently holds key status, i.e. whether typing reaches it.
///
/// Read-only and touches nothing winit owns, so unlike the mutating helpers it is safe to call
/// synchronously from inside a frame.
pub fn is_key_window(handle: RawWindowHandle) -> bool {
    window_from_handle(handle).is_some_and(|window| window.isKeyWindow())
}

/// The current hour (0-23) in the user's local time zone.
///
/// Uses `NSCalendar` rather than hand-rolling an offset from `SystemTime`, so daylight saving and
/// time-zone changes are handled by the system.
pub fn local_hour() -> u8 {
    let calendar = objc2_foundation::NSCalendar::currentCalendar();
    let now = objc2_foundation::NSDate::now();
    let hour = unsafe {
        calendar.component_fromDate(objc2_foundation::NSCalendarUnit::Hour, &now)
    };
    hour.clamp(0, 23) as u8
}

/// Float the panel above other windows, or let it sit among them.
///
/// The panel is only pinned on top while it has focus. Once the user clicks another window,
/// staying above it would be obstructive — the launcher is not a utility palette for another app,
/// it is a transient thing the user is either using or not.
pub fn set_floating(handle: RawWindowHandle, floating: bool) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || set_floating_now(handle.get(), floating));
}

fn set_floating_now(handle: RawWindowHandle, floating: bool) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    let level = if floating {
        FLOATING_WINDOW_LEVEL
    } else {
        NORMAL_WINDOW_LEVEL
    };
    window.setLevel(level);
    if let Some(backdrop) = backdrop_window() {
        backdrop.setLevel(level);
    }
    if std::env::var("PS_DEBUG").is_ok() {
        eprintln!("window level -> {} (floating={floating})", window.level());
    }
}

/// Let the user move the window by dragging it, which `apply_panel_chrome` turns off.
///
/// The launcher panel is placed by code and should stay put, but the register form is a normal
/// little dialog — it needs `movable` back on for AppKit to honour the drag egui starts.
pub fn set_movable(handle: RawWindowHandle, movable: bool) {
    let handle = MainThreadHandle(handle);
    on_main_queue(move || set_movable_now(handle.get(), movable));
}

fn set_movable_now(handle: RawWindowHandle, movable: bool) {
    let Some(window) = window_from_handle(handle) else {
        return;
    };
    window.setMovable(movable);
}
