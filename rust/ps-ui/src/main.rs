mod app;
mod daemon;
mod theme;
mod watcher;

use anyhow::Result;
use app::{Launcher, Outcome};
use daemon::Command;
use eframe::egui;
use raw_window_handle::HasWindowHandle;
use ps_core::{paths, Actions, Index, UsageStats};
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
        Some("daemon") => run(true),
        Some("ui") => run(false),
        Some("search") => search(&args[1..].join(" ")),
        None => run(false),
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
    Index::load(&paths::entries_dump())
}

fn run(as_daemon: bool) -> Result<()> {
    // Entries are loaded once, here, into memory. Nothing on the search path ever reads a file or
    // spawns a process.
    let index = match load_index() {
        Ok(index) => index,
        Err(error) if as_daemon => {
            // First run, or the dump was removed: generate it before giving up.
            eprintln!("{error}; generating entries dump");
            let mut child = Actions::resolve().dump_entries()?;
            child.wait()?;
            load_index()?
        }
        Err(error) => return Err(error),
    };

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

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([Metrics::WINDOW_WIDTH, Metrics::window_height(0)])
            .with_decorations(false)
            .with_transparent(true)
            .with_resizable(false)
            .with_visible(!as_daemon),
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

            // Regenerate the dump whenever the entries sources change on disk.
            let watcher = watcher::entries_project_root().and_then(|root| {
                let pending = pending_for_app.clone();
                let ctx = cc.egui_ctx.clone();
                watcher::watch_entries(root, move || {
                    if let Ok(fresh) = load_index() {
                        *pending.lock().unwrap() = Some(fresh);
                        ctx.request_repaint();
                    }
                })
                .map_err(|error| eprintln!("entries watcher disabled: {error}"))
                .ok()
            });

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
                last_height: 0.0,
                _watcher: watcher,
            }))
        }),
    )
    .map_err(|error| anyhow::anyhow!("{error}"))
}

/// Regenerate the entries dump and load it, off the UI thread.
///
/// The dump costs ~150 ms of Python, so doing it inline would freeze the window — including the
/// spinner that is supposed to show it is working.
fn reload_in_background(
    pending: Arc<Mutex<Option<Index>>>,
    ctx: egui::Context,
) {
    std::thread::spawn(move || {
        match Actions::resolve().dump_entries() {
            Ok(mut child) => {
                let _ = child.wait();
            }
            Err(error) => eprintln!("could not run entries dump: {error}"),
        }
        match load_index() {
            Ok(fresh) => *pending.lock().unwrap() = Some(fresh),
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
    _watcher: Option<Box<dyn std::any::Any>>,
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
            let is_key = ps_mac::is_key_window(handle);

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
                ctx.send_viewport_cmd(egui::ViewportCommand::Close);
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
