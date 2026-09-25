//! Minimal standalone form for registering a new PythonSearch entry.
//!
//! Deliberately its own process rather than a mode of `ps_ui`: the launcher is a resident daemon
//! with a hidden window it toggles, and bolting a second, independently-shown window onto that
//! state machine is more risk than a five-field form is worth. This just opens, saves, and exits.
//!
//! Styled to match the launcher panel (same fonts, palette, rounded vibrancy chrome) so the two
//! feel like one app, even though this is a separate borderless window.

#[path = "../theme.rs"]
#[allow(dead_code)]
mod theme;

use eframe::egui;
use egui::{Color32, CornerRadius, Stroke};
use ps_core::Actions;
use raw_window_handle::HasWindowHandle;
use theme::{Metrics, Palette};

const WINDOW_WIDTH: f32 = 460.0;
const WINDOW_HEIGHT: f32 = 420.0;
const VALUE_ROWS: usize = 10;
/// Breathing room between the window edge and the form, and between the form and the button row.
const OUTER_MARGIN: i8 = 22;
const BUTTON_ROW_GAP: f32 = 22.0;

const TYPES: [&str; 5] = ["snippet", "cli_cmd", "cmd", "url", "file"];

fn main() -> eframe::Result<()> {
    let clipboard = read_clipboard();
    let default_type = if clipboard.starts_with("http") { "url" } else { "snippet" };

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([WINDOW_WIDTH, WINDOW_HEIGHT])
            .with_decorations(false)
            .with_transparent(true)
            .with_resizable(false)
            .with_title("Register New Entry")
            // Created hidden so it can be moved to its final position before it is ever shown —
            // otherwise it flashes at whatever spot the OS defaults to and then jumps to centre.
            .with_visible(false),
        ..Default::default()
    };

    eframe::run_native(
        "PythonSearch — Register New Entry",
        options,
        Box::new(move |cc| {
            theme::install(&cc.egui_ctx);
            // `theme::install` only defines the launcher's own named text styles and zeroes item
            // spacing for its hand-painted rows; this form uses ordinary widgets (buttons, combo
            // boxes) that need the styles egui ships by default, plus their normal spacing back.
            let defaults = egui::Style::default().text_styles;
            cc.egui_ctx.all_styles_mut(|style| {
                for (text_style, font_id) in &defaults {
                    style
                        .text_styles
                        .entry(text_style.clone())
                        .or_insert_with(|| font_id.clone());
                }
                style.spacing.item_spacing = egui::vec2(8.0, 8.0);
            });
            ps_mac::hide_from_dock();
            Ok(Box::new(RegisterForm {
                key: String::new(),
                value: clipboard,
                entry_type: default_type.to_string(),
                actions: Actions::resolve(),
                positioned: false,
                chrome_applied: false,
                key_focused: false,
                dark: theme::dark_mode_now(),
                saving: false,
                error: None,
                save_rx: None,
            }))
        }),
    )
}

fn read_clipboard() -> String {
    std::process::Command::new("pbpaste")
        .output()
        .map(|out| String::from_utf8_lossy(&out.stdout).trim_end().to_string())
        .unwrap_or_default()
}

struct RegisterForm {
    key: String,
    value: String,
    entry_type: String,
    actions: Actions,
    /// Positioning and chrome need a window handle, which is only reachable once eframe has
    /// created the native window — so both happen on the first `logic` call, not at construction.
    positioned: bool,
    chrome_applied: bool,
    key_focused: bool,
    dark: bool,
    /// Set while the background save is in flight, so the button can show it is doing something
    /// instead of looking like the click did nothing for the ~100-300ms Python takes to start.
    saving: bool,
    /// Last save failure, if any — shown inline rather than swallowed, since a fire-and-forget
    /// spawn here previously hid real errors (bad key, binary not found) as "nothing happened".
    error: Option<String>,
    save_rx: Option<std::sync::mpsc::Receiver<Result<(), String>>>,
}

impl RegisterForm {
    /// Runs `register_new` on a background thread — it shells out to Python, which is slow enough
    /// to freeze the window for a click if run inline — and reports back through `save_rx`.
    fn submit(&mut self, ctx: egui::Context) {
        self.saving = true;
        self.error = None;

        let (tx, rx) = std::sync::mpsc::channel();
        self.save_rx = Some(rx);

        let actions = self.actions.clone();
        let key = self.key.trim().to_string();
        let value = self.value.clone();
        let entry_type = self.entry_type.clone();
        std::thread::spawn(move || {
            let result = actions.register_new(&key, &value, &entry_type);
            let _ = tx.send(result);
            ctx.request_repaint();
        });
    }

    /// Pick up the background save's result, if it has landed yet.
    fn poll_save(&mut self) {
        let Some(rx) = &self.save_rx else {
            return;
        };
        let Ok(result) = rx.try_recv() else {
            return;
        };
        self.save_rx = None;
        self.saving = false;
        match result {
            Ok(()) => std::process::exit(0),
            Err(message) => self.error = Some(message),
        }
    }

    fn can_save(&self) -> bool {
        !self.saving && !self.key.trim().is_empty()
    }

    fn palette(&self) -> Palette {
        if self.dark { Palette::dark() } else { Palette::light() }
    }
}

impl eframe::App for RegisterForm {
    /// Fully transparent so the window's vibrancy layer shows through, same as the launcher panel.
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0.0, 0.0, 0.0, 0.0]
    }

    /// Window placement and chrome need a real window handle, which `logic` (run outside the egui
    /// pass) is where the rest of this codebase does that kind of AppKit work.
    ///
    /// The window starts hidden (see `with_visible(false)` above), so it can be centred and only
    /// then revealed — that ordering is what keeps it from flashing at the OS-default spot first.
    fn logic(&mut self, ctx: &egui::Context, frame: &mut eframe::Frame) {
        let Ok(handle) = frame.window_handle() else {
            return;
        };
        let handle = handle.as_raw();

        if !self.chrome_applied {
            self.chrome_applied = true;
            ps_mac::apply_panel_chrome(handle, Metrics::CORNER_RADIUS as f64);
            // The panel chrome pins the launcher in place; this form is an ordinary little dialog
            // the user should be able to shove out of the way, so hand `movable` back.
            ps_mac::set_movable(handle, true);
        }

        if !self.positioned {
            self.positioned = true;
            ps_mac::center_on_main_screen(handle, WINDOW_WIDTH as f64, WINDOW_HEIGHT as f64);
            ps_mac::order_front(handle);
            ctx.send_viewport_cmd(egui::ViewportCommand::Visible(true));
        }
    }

    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        self.poll_save();
        self.dark = theme::dark_mode_now();
        let palette = self.palette();

        if ui.ctx().input(|i| i.key_pressed(egui::Key::Escape)) {
            std::process::exit(0);
        }

        // The panel's own background, painted before anything else — same trick the launcher uses
        // to read solidly over the transparent vibrancy backdrop instead of see-through.
        ui.painter().rect_filled(
            ui.ctx().viewport_rect(),
            CornerRadius::same(Metrics::CORNER_RADIUS as u8),
            palette.panel_bg,
        );

        // The window has no titlebar to grab (see `with_decorations(false)`), so dragging any
        // empty spot on the panel moves it. Registered before the form's widgets so that a widget
        // under the cursor wins the interaction and text selection still works.
        let background = ui.interact(
            ui.ctx().viewport_rect(),
            ui.id().with("window_drag"),
            egui::Sense::drag(),
        );
        if background.drag_started() {
            ui.ctx().send_viewport_cmd(egui::ViewportCommand::StartDrag);
        }

        style_widgets(ui, &palette);

        let frame = egui::Frame::NONE.inner_margin(OUTER_MARGIN);
        frame.show(ui, |ui| {
            ui.colored_label(palette.text_dim, "Key");
            let key_field = ui.add(
                egui::TextEdit::singleline(&mut self.key)
                    .desired_width(f32::INFINITY)
                    .hint_text("entry key"),
            );
            if !self.key_focused {
                key_field.request_focus();
                self.key_focused = true;
            }
            // Enter submits from the key field, mirroring how the launcher's own query field acts
            // on Enter — the value field below keeps Enter as a plain newline.
            let submitted =
                key_field.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter));

            ui.add_space(2.0);
            ui.colored_label(palette.text_dim, "Value");
            ui.add(
                egui::TextEdit::multiline(&mut self.value)
                    .desired_width(f32::INFINITY)
                    .desired_rows(VALUE_ROWS),
            );

            ui.add_space(2.0);
            ui.horizontal(|ui| {
                ui.colored_label(palette.text_dim, "Type");
                egui::ComboBox::from_id_salt("entry_type")
                    .selected_text(&self.entry_type)
                    .show_ui(ui, |ui| {
                        for candidate in TYPES {
                            ui.selectable_value(&mut self.entry_type, candidate.to_string(), candidate);
                        }
                    });
            });

            ui.add_space(BUTTON_ROW_GAP - 2.0);
            let clicked_save = ui
                .horizontal(|ui| {
                    let button_size = egui::vec2(90.0, 30.0);
                    let can_save = self.can_save();
                    let label = if self.saving { "Saving…" } else { "Save" };
                    let save_clicked = ui
                        .add_enabled(can_save, egui::Button::new(label).min_size(button_size))
                        .clicked();
                    if ui
                        .add(egui::Button::new("Cancel (Esc)").min_size(button_size))
                        .clicked()
                    {
                        std::process::exit(0);
                    }
                    save_clicked
                })
                .inner;

            if (clicked_save || submitted) && self.can_save() {
                self.submit(ui.ctx().clone());
            }

            if let Some(error) = &self.error {
                ui.add_space(8.0);
                ui.colored_label(Color32::from_rgb(0xFF, 0x6B, 0x6B), error);
            }
        });
    }
}

/// Recolour the default egui widgets to the launcher's palette instead of egui's own defaults,
/// since this form uses ordinary widgets rather than the launcher's hand-painted rows.
fn style_widgets(ui: &mut egui::Ui, palette: &Palette) {
    let visuals = &mut ui.style_mut().visuals;
    visuals.override_text_color = Some(palette.text);
    visuals.extreme_bg_color = palette.chip_bg;
    visuals.selection.bg_fill = palette.accent;
    visuals.selection.stroke = Stroke::new(1.0, Color32::WHITE);

    let widgets = &mut visuals.widgets;
    for style in [
        &mut widgets.inactive,
        &mut widgets.hovered,
        &mut widgets.active,
        &mut widgets.open,
    ] {
        style.bg_fill = palette.chip_bg;
        style.weak_bg_fill = palette.chip_bg;
        style.bg_stroke = Stroke::new(1.0, palette.separator);
        style.fg_stroke = Stroke::new(1.0, palette.text);
    }
    widgets.hovered.bg_stroke = Stroke::new(1.0, palette.accent);
    widgets.active.bg_fill = palette.accent;
    widgets.active.weak_bg_fill = palette.accent;
    widgets.active.fg_stroke = Stroke::new(1.0, Color32::WHITE);
}
