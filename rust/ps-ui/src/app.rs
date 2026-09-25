use crate::theme::{text, Metrics, Palette};
use egui::{
    text::LayoutJob, Align, Align2, Color32, CornerRadius, FontSelection, Key, Layout, Modifiers,
    Rect, RichText, Stroke, TextFormat, TextStyle, Ui, Vec2,
};
use ps_core::{usage::MAX_QUERY_HISTORY, Actions, Index, Match};

/// How long the "Copied" toast stays on screen before the panel hides itself.
const COPY_FLASH_SECONDS: f64 = 0.45;

/// What the user asked the launcher to do with the selected row.
pub enum Outcome {
    None,
    /// The window should hide; the daemon restores focus to the previous app.
    Hide,
}

pub struct Launcher {
    index: Index,
    actions: Actions,
    query: String,
    /// True when the whole query is selected, so the next character typed replaces it.
    /// The query field has no caret positioning, so select-all is the only selection state there
    /// is — which is all that "select what I typed and overwrite it" needs.
    query_selected: bool,
    matches: Vec<Match>,
    selected: usize,
    scroll_offset: usize,
    palette: Palette,
    /// Set when a reload was requested, so the daemon can pick it up.
    pub reload_requested: bool,
    /// Whether the panel holds keyboard focus. Drives the inactive styling.
    focused: bool,
    /// A reload is in flight; the hint row shows a spinner until it lands.
    reloading: bool,
    /// Transient confirmation shown in the hint row: (message, when it was set).
    toast: Option<(String, f64)>,
    /// When copying should hide the panel, once the "Copied" toast has had a moment to be seen.
    copy_hide_at: Option<f64>,
    /// Queries that previously led to a run, most recent first. Arrowing up past the first row
    /// walks this, as the terminal UI does.
    query_history: Vec<String>,
    /// Where in `query_history` the current query came from, if it came from there at all.
    history_index: Option<usize>,
}

impl Launcher {
    pub fn new(index: Index, actions: Actions, dark_mode: bool) -> Self {
        let mut launcher = Launcher {
            index,
            actions,
            query: String::new(),
            query_selected: false,
            matches: Vec::new(),
            selected: 0,
            scroll_offset: 0,
            palette: if dark_mode {
                Palette::dark()
            } else {
                Palette::light()
            },
            reload_requested: false,
            focused: true,
            reloading: false,
            toast: None,
            copy_hide_at: None,
            query_history: Vec::new(),
            history_index: None,
        };
        launcher.research();
        launcher
    }

    /// Track whether typing would actually reach the panel.
    pub fn set_focused(&mut self, focused: bool) {
        self.focused = focused;
    }

    pub fn set_reloading(&mut self, reloading: bool) {
        self.reloading = reloading;
    }

    /// Show a short confirmation in the hint row. `now` comes from the egui clock so the fade is
    /// driven by the same time base as the rest of the UI.
    pub fn show_toast(&mut self, message: impl Into<String>, now: f64) {
        self.reloading = false;
        self.toast = Some((message.into(), now));
    }

    pub fn set_dark_mode(&mut self, dark: bool) {
        self.palette = if dark {
            Palette::dark()
        } else {
            Palette::light()
        };
    }

    /// Seed the history from disk once the usage load finishes.
    pub fn set_query_history(&mut self, history: Vec<String>) {
        self.query_history = history;
        self.history_index = None;
    }

    pub fn replace_index(&mut self, index: Index) {
        self.index = index;
        self.research();
    }

    pub fn index_mut(&mut self) -> &mut Index {
        &mut self.index
    }

    /// Clear back to the state the window should open in.
    pub fn reset(&mut self) {
        self.query.clear();
        self.query_selected = false;
        self.history_index = None;
        self.selected = 0;
        self.scroll_offset = 0;
        self.research();
    }

    fn research(&mut self) {
        self.matches = self.index.search(&self.query);
        self.selected = 0;
        self.scroll_offset = 0;
    }

    /// Height the window should have for the current result count.
    pub fn desired_height(&self) -> f32 {
        Metrics::window_height(self.visible_rows())
    }

    fn visible_rows(&self) -> usize {
        self.matches.len().min(Metrics::MAX_VISIBLE_ROWS)
    }

    pub fn ui(&mut self, ui: &mut Ui) -> Outcome {
        let outcome = self.handle_keys(ui.ctx());

        // The panel's own background, painted before anything else. Without it the window is just
        // the transparent render surface over the vibrancy backdrop, which reads as see-through.
        ui.painter().rect_filled(
            ui.ctx().viewport_rect(),
            CornerRadius::same(Metrics::CORNER_RADIUS as u8),
            self.palette.panel_bg,
        );

        self.query_row(ui);
        let activated = if self.matches.is_empty() {
            false
        } else {
            self.separator(ui);
            let activated = self.result_rows(ui);
            self.separator(ui);
            self.hint_row(ui);
            activated
        };

        // Run after the rows are laid out, so the click handling does not borrow across the paint.
        if activated && self.run_selected() {
            return Outcome::Hide;
        }

        if let Some(hide_at) = self.copy_hide_at {
            let now = ui.ctx().input(|i| i.time);
            if now >= hide_at {
                self.copy_hide_at = None;
                return Outcome::Hide;
            }
            ui.ctx().request_repaint();
        }

        outcome
    }

    fn separator(&self, ui: &mut Ui) {
        let (rect, _) = ui.allocate_exact_size(egui::vec2(ui.available_width(), 1.0), egui::Sense::hover());
        ui.painter()
            .rect_filled(rect, CornerRadius::ZERO, self.palette.separator);
    }

    fn query_row(&mut self, ui: &mut Ui) {
        let (rect, _) = ui.allocate_exact_size(
            egui::vec2(ui.available_width(), Metrics::QUERY_ROW_HEIGHT),
            egui::Sense::hover(),
        );
        let painter = ui.painter();
        let mid = rect.center().y;

        // Magnifier glyph, drawn rather than typed so the look does not depend on an icon font.
        let glyph_center = egui::pos2(rect.left() + Metrics::SIDE_PADDING + 9.0, mid);
        painter.circle_stroke(glyph_center, 8.0, Stroke::new(1.8, self.palette.text_faint));
        painter.line_segment(
            [
                glyph_center + Vec2::new(5.8, 5.8),
                glyph_center + Vec2::new(11.0, 11.0),
            ],
            Stroke::new(1.8, self.palette.text_faint),
        );

        let text_left = rect.left() + Metrics::SIDE_PADDING + 34.0;
        let font = TextStyle::Name(text::QUERY.into()).resolve(ui.style());

        let text_width = if self.query.is_empty() {
            painter.text(
                // Offset so the placeholder clears the caret sitting at the start of the field.
                egui::pos2(text_left + 14.0, mid),
                Align2::LEFT_CENTER,
                "Search entries",
                font.clone(),
                self.palette.text_faint,
            );
            0.0
        } else {
            let galley = painter.layout_no_wrap(
                self.query.clone(),
                font.clone(),
                if self.query_selected {
                    self.palette.selected_text
                } else {
                    self.palette.text
                },
            );
            let size = galley.size();
            let origin = egui::pos2(text_left, mid - size.y / 2.0);

            if self.query_selected {
                // Standard text-selection fill, so it is obvious the next keystroke overwrites.
                painter.rect_filled(
                    Rect::from_min_size(origin - Vec2::new(2.0, 2.0), size + Vec2::new(4.0, 4.0)),
                    CornerRadius::same(3),
                    self.palette.selection_for(self.focused),
                );
            }

            painter.galley(origin, galley, Color32::WHITE);
            size.x
        };

        // A selection stands in for the caret, as in any other text field. Otherwise the caret
        // blinks at the usual macOS cadence, including on an empty field.
        // An unfocused text field shows no caret on macOS, which is half the focus cue.
        if !self.query_selected && self.focused {
            let period = 1.06;
            let phase = ui.input(|i| i.time) % period;
            if phase < period / 2.0 {
                let caret_x = text_left + text_width + 2.0;
                painter.line_segment(
                    [
                        egui::pos2(caret_x, mid - font.size * 0.55),
                        egui::pos2(caret_x, mid + font.size * 0.55),
                    ],
                    Stroke::new(1.6, self.palette.accent),
                );
            }
            // Wake up in time for the next blink edge rather than repainting continuously.
            let until_next_edge = (period / 2.0) - (phase % (period / 2.0));
            ui.ctx()
                .request_repaint_after(std::time::Duration::from_secs_f64(until_next_edge.max(0.01)));
        }
    }

    /// Returns true when a row was double-clicked, which runs it just like Enter.
    fn result_rows(&mut self, ui: &mut Ui) -> bool {
        let visible = self.visible_rows();
        let mut activated = false;
        for offset in 0..visible {
            let match_index = self.scroll_offset + offset;
            if match_index >= self.matches.len() {
                break;
            }
            activated |= self.result_row(ui, match_index);
        }
        activated
    }

    /// Returns true when this row was double-clicked.
    fn result_row(&mut self, ui: &mut Ui, match_index: usize) -> bool {
        let (rect, response) = ui.allocate_exact_size(
            egui::vec2(ui.available_width(), Metrics::ROW_HEIGHT),
            egui::Sense::click(),
        );

        // A single click selects, a double click runs — the usual list behaviour.
        if response.clicked() || response.double_clicked() {
            self.selected = match_index;
        }
        let activated = response.double_clicked();

        if response.hovered() {
            ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
        }

        let selected = match_index == self.selected;

        let m = &self.matches[match_index];
        let entry = self.index.entry(m.index);
        let painter = ui.painter();

        if selected {
            let fill_rect = Rect::from_min_max(
                egui::pos2(rect.left() + 8.0, rect.top() + 3.0),
                egui::pos2(rect.right() - 8.0, rect.bottom() - 3.0),
            );
            painter.rect_filled(
                fill_rect,
                CornerRadius::same(8),
                self.palette.selection_for(self.focused),
            );
        }

        let mid = rect.center().y;
        let mut cursor_x = rect.left() + Metrics::SIDE_PADDING;

        // Type chip.
        let chip_font = TextStyle::Name(text::CHIP.into()).resolve(ui.style());
        let label = entry.entry_type.label();
        let chip_galley = painter.layout_no_wrap(
            label.to_string(),
            chip_font,
            if selected {
                Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0xDD)
            } else {
                self.palette.text_dim
            },
        );
        let chip_width = 40.0;
        let chip_rect = Rect::from_center_size(
            egui::pos2(cursor_x + chip_width / 2.0, mid),
            egui::vec2(chip_width, 18.0),
        );
        if !selected {
            painter.rect_filled(chip_rect, CornerRadius::same(5), self.palette.chip_bg);
        } else {
            painter.rect_stroke(
                chip_rect,
                CornerRadius::same(5),
                Stroke::new(1.0, Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0x55)),
                egui::StrokeKind::Inside,
            );
        }
        painter.galley(
            egui::pos2(
                chip_rect.center().x - chip_galley.size().x / 2.0,
                mid - chip_galley.size().y / 2.0,
            ),
            chip_galley,
            Color32::WHITE,
        );
        cursor_x += chip_width + 14.0;

        // Key, with matched characters emphasised.
        let key_width = (rect.width() * 0.46).min(340.0);
        let key_job = self.key_layout(ui, entry.key.as_str(), &m.key_indices, selected, key_width);
        let key_galley = painter.layout_job(key_job);
        painter.galley(
            egui::pos2(cursor_x, mid - key_galley.size().y / 2.0),
            key_galley,
            Color32::WHITE,
        );
        cursor_x += key_width + 16.0;

        // Shortcut hint, if the entry has one bound via Karabiner.
        let mut right_edge = rect.right() - Metrics::SIDE_PADDING;
        if let Some(shortcut) = entry.shortcut() {
            let font = TextStyle::Name(text::CHIP.into()).resolve(ui.style());
            let galley = painter.layout_no_wrap(
                shortcut.to_string(),
                font,
                if selected {
                    Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0xCC)
                } else {
                    self.palette.text_faint
                },
            );
            let width = galley.size().x;
            painter.galley(
                egui::pos2(right_edge - width, mid - galley.size().y / 2.0),
                galley,
                Color32::WHITE,
            );
            right_edge -= width + 16.0;
        }

        // Content, filling whatever horizontal space is left.
        let content_width = (right_edge - cursor_x).max(0.0);
        if content_width > 30.0 {
            let font = TextStyle::Name(text::CONTENT.into()).resolve(ui.style());
            let mut galley = painter.layout_no_wrap(
                entry.display_content().to_string(),
                font.clone(),
                self.palette.content_on(selected),
            );
            if galley.size().x > content_width {
                let truncated = truncate_to_width(ui, entry.display_content(), &font, content_width);
                galley = painter.layout_no_wrap(truncated, font, self.palette.content_on(selected));
            }
            painter.galley(
                egui::pos2(cursor_x, mid - galley.size().y / 2.0),
                galley,
                Color32::WHITE,
            );
        }

        activated
    }

    /// Lay out the key with the fuzzy-matched characters in the medium weight and full colour, and
    /// the rest dimmed. This is what makes it obvious *why* a row matched.
    fn key_layout(
        &self,
        ui: &Ui,
        key: &str,
        matched: &[u32],
        selected: bool,
        max_width: f32,
    ) -> LayoutJob {
        let base_font = TextStyle::Name(text::KEY.into()).resolve(ui.style());
        let strong = self.palette.key_on(selected);
        let weak = if selected {
            Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0xB0)
        } else {
            self.palette.text_dim
        };

        let mut job = LayoutJob::default();
        job.wrap.max_width = max_width;
        job.wrap.max_rows = 1;
        job.wrap.break_anywhere = true;

        for (position, character) in key.chars().enumerate() {
            let is_match = matched.binary_search(&(position as u32)).is_ok();
            job.append(
                &character.to_string(),
                0.0,
                TextFormat {
                    font_id: base_font.clone(),
                    color: if is_match { strong } else { weak },
                    ..Default::default()
                },
            );
        }
        job
    }

    fn hint_row(&self, ui: &mut Ui) {
        let (rect, _) = ui.allocate_exact_size(
            egui::vec2(ui.available_width(), Metrics::HINT_ROW_HEIGHT),
            egui::Sense::hover(),
        );
        let painter = ui.painter();
        let font = TextStyle::Name(text::HINT.into()).resolve(ui.style());
        let mid = rect.center().y;

        painter.text(
            egui::pos2(rect.left() + Metrics::SIDE_PADDING, mid),
            Align2::LEFT_CENTER,
            "↩ open      ⌘C copy      Tab edit      ^G google      Esc / ^C close",
            font.clone(),
            self.palette.text_faint,
        );
        let now = ui.input(|i| i.time);
        let right = egui::pos2(rect.right() - Metrics::SIDE_PADDING, mid);

        if self.reloading {
            // Spinner: a rotating arc, so it is obvious the reload is actually running.
            let centre = egui::pos2(right.x - 58.0, mid);
            let turns = now * 1.4;
            for step in 0..8 {
                let angle = turns * std::f64::consts::TAU + step as f64 * std::f64::consts::TAU / 8.0;
                let fade = 1.0 - step as f32 / 8.0;
                painter.circle_filled(
                    centre + Vec2::new(angle.cos() as f32 * 5.0, angle.sin() as f32 * 5.0),
                    1.4,
                    self.palette.accent.gamma_multiply(fade),
                );
            }
            painter.text(
                right,
                Align2::RIGHT_CENTER,
                "Reloading",
                font,
                self.palette.text_dim,
            );
            ui.ctx().request_repaint();
        } else if let Some((message, shown_at)) = &self.toast {
            // Hold for a moment, then fade out.
            const HOLD: f64 = 1.4;
            const FADE: f64 = 0.7;
            let age = now - shown_at;
            if age < HOLD + FADE {
                let alpha = if age <= HOLD {
                    1.0
                } else {
                    1.0 - ((age - HOLD) / FADE) as f32
                };
                painter.text(
                    right,
                    Align2::RIGHT_CENTER,
                    message,
                    font,
                    self.palette.accent.gamma_multiply(alpha),
                );
                ui.ctx().request_repaint();
            } else {
                painter.text(
                    right,
                    Align2::RIGHT_CENTER,
                    format!("{} of {}", self.matches.len(), self.index.len()),
                    font,
                    self.palette.text_faint,
                );
            }
        } else {
            painter.text(
                right,
                Align2::RIGHT_CENTER,
                format!("{} of {}", self.matches.len(), self.index.len()),
                font,
                self.palette.text_faint,
            );
        }
    }

    fn handle_keys(&mut self, ctx: &egui::Context) -> Outcome {
        let mut outcome = Outcome::None;
        let mut query_changed = false;

        let events = ctx.input(|i| i.events.clone());
        for event in events {
            if debug_enabled() {
                if let egui::Event::Key { key, pressed, modifiers, repeat, .. } = &event {
                    eprintln!(
                        "key {key:?} pressed={pressed} repeat={repeat} cmd={} ctrl={} alt={}",
                        modifiers.command, modifiers.ctrl, modifiers.alt
                    );
                } else if let egui::Event::Text(text) = &event {
                    eprintln!("text {text:?}");
                } else if let egui::Event::PointerButton {
                    pos,
                    button,
                    pressed,
                    ..
                } = &event
                {
                    eprintln!("pointer {button:?} pressed={pressed} at {pos:?}");
                }
            }
            match event {
                egui::Event::Text(text) => {
                    // Modifier combinations arrive as Key events; only real typing lands here, so
                    // every printable character stays usable as query text.
                    if self.query_selected {
                        self.query.clear();
                        self.query_selected = false;
                    }
                    self.query.push_str(&text);
                    self.history_index = None;
                    query_changed = true;
                }
                egui::Event::Key {
                    key,
                    pressed: true,
                    modifiers,
                    ..
                } => {
                    match (key, modifiers.command, modifiers.ctrl) {
                        // Ctrl+C dismisses, as it exits the terminal UI. ⌘C is copy, separately.
                        (Key::Escape, _, _) | (Key::C, false, true) => outcome = Outcome::Hide,
                        (Key::Backspace, true, _) => {
                            if let Some(key) = self.selected_key() {
                                self.actions.delete_key(&key);
                                outcome = Outcome::Hide;
                            }
                        }
                        (Key::Backspace, _, _) => {
                            if self.query_selected {
                                self.query.clear();
                                self.query_selected = false;
                            } else {
                                self.query.pop();
                            }
                            self.history_index = None;
                            query_changed = true;
                        }
                        (Key::Enter, _, _) => {
                            if self.run_selected() {
                                outcome = Outcome::Hide;
                            }
                        }
                        (Key::Tab, _, _) => {
                            if let Some(key) = self.selected_key() {
                                self.actions.edit_key(&key);
                                outcome = Outcome::Hide;
                            }
                        }
                        (Key::A, true, _) => self.query_selected = !self.query.is_empty(),
                        (Key::G, _, true) => {
                            // Ctrl+G googles the query, the equivalent of `?` in the terminal UI.
                            if !self.query.trim().is_empty() {
                                self.actions.search_in_google(&self.query);
                                outcome = Outcome::Hide;
                            }
                        }
                        (Key::C, true, _) => {
                            if let Some(key) = self.selected_key() {
                                self.actions.copy_value(&key);
                                let now = ctx.input(|i| i.time);
                                self.show_toast("Copied", now);
                                // Hide shortly after, once the toast has had a moment to register,
                                // rather than instantly — otherwise the confirmation never renders.
                                self.copy_hide_at = Some(now + COPY_FLASH_SECONDS);
                            }
                        }
                        (Key::R, true, _) | (Key::R, _, true) => self.reload_requested = true,
                        (Key::ArrowDown, _, _) | (Key::N, _, true) => self.move_selection(1),
                        (Key::ArrowUp, _, _) | (Key::P, _, true) => {
                            if self.selected > 0 {
                                self.move_selection(-1);
                                self.history_index = None;
                            } else if self.recall_previous_query() {
                                query_changed = true;
                            }
                        }
                        (Key::Num1, true, _) => self.run_index(0, &mut outcome),
                        (Key::Num2, true, _) => self.run_index(1, &mut outcome),
                        (Key::Num3, true, _) => self.run_index(2, &mut outcome),
                        (Key::Num4, true, _) => self.run_index(3, &mut outcome),
                        (Key::Num5, true, _) => self.run_index(4, &mut outcome),
                        (Key::Num6, true, _) => self.run_index(5, &mut outcome),
                        (Key::Num7, true, _) => self.run_index(6, &mut outcome),
                        (Key::Num8, true, _) => self.run_index(7, &mut outcome),
                        (Key::Num9, true, _) => self.run_index(8, &mut outcome),
                        (Key::U, _, true) => {
                            self.query.clear();
                            self.query_selected = false;
                            self.history_index = None;
                            query_changed = true;
                        }
                        (Key::W, _, true) => {
                            // Drop the trailing word, matching readline.
                            let trimmed = self.query.trim_end();
                            let cut = trimmed.rfind(' ').map(|i| i + 1).unwrap_or(0);
                            self.query.truncate(cut);
                            self.query_selected = false;
                            self.history_index = None;
                            query_changed = true;
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        }

        // Mouse wheel scrolling through a long result list.
        let scroll = ctx.input(|i| i.smooth_scroll_delta.y);
        if scroll.abs() > 1.0 {
            self.move_selection(if scroll < 0.0 { 1 } else { -1 });
        }

        if query_changed {
            self.matches = self.index.search(&self.query);
            self.selected = 0;
            self.scroll_offset = 0;
        }

        // Ignore modifier-only presses: the tuple match above is exhaustive but a stray Cmd tap
        // should not count as an action.
        let _ = Modifiers::default();
        outcome
    }

    fn run_index(&mut self, index: usize, outcome: &mut Outcome) {
        if index < self.matches.len() {
            self.selected = index;
            if self.run_selected() {
                *outcome = Outcome::Hide;
            }
        }
    }

    fn selected_key(&self) -> Option<String> {
        self.matches
            .get(self.selected)
            .map(|m| self.index.entry(m.index).key.clone())
    }

    fn run_selected(&mut self) -> bool {
        let Some(key) = self.selected_key() else {
            return false;
        };
        self.actions.run_key(&key);
        let timestamp = ps_core::actions::log_run(&key, &self.query);
        self.index.record_run(&key, timestamp);
        self.remember_query();
        true
    }

    /// Replace the query with the next older entry from the run history, wrapping at the end.
    /// Returns whether the query changed.
    fn recall_previous_query(&mut self) -> bool {
        if self.query_history.is_empty() {
            return false;
        }
        let next = match self.history_index {
            None => 0,
            Some(index) => (index + 1) % self.query_history.len(),
        };
        self.history_index = Some(next);
        self.query = self.query_history[next].clone();
        self.query_selected = false;
        true
    }

    /// Push the query that produced a run to the front of the history, without duplicates.
    fn remember_query(&mut self) {
        if self.query.trim().is_empty() {
            return;
        }
        self.query_history.retain(|past| past != &self.query);
        self.query_history.insert(0, self.query.clone());
        self.query_history.truncate(MAX_QUERY_HISTORY);
        self.history_index = None;
    }

    fn move_selection(&mut self, delta: i32) {
        if self.matches.is_empty() {
            return;
        }
        let last = self.matches.len() - 1;
        self.selected = (self.selected as i32 + delta).clamp(0, last as i32) as usize;

        // Keep the selection inside the visible window.
        if self.selected < self.scroll_offset {
            self.scroll_offset = self.selected;
        } else if self.selected >= self.scroll_offset + Metrics::MAX_VISIBLE_ROWS {
            self.scroll_offset = self.selected - Metrics::MAX_VISIBLE_ROWS + 1;
        }
    }
}

/// Cut `value` to whatever fits in `max_width`, with a trailing ellipsis.
///
/// Binary search over character counts rather than a per-glyph walk: glyph advances are only
/// reachable through a mutable font view, and a handful of layout calls is cheaper than the
/// borrow gymnastics.
fn truncate_to_width(ui: &Ui, value: &str, font: &egui::FontId, max_width: f32) -> String {
    let measure = |count: usize| -> f32 {
        let candidate: String = value.chars().take(count).chain(std::iter::once('…')).collect();
        ui.painter()
            .layout_no_wrap(candidate, font.clone(), Color32::WHITE)
            .size()
            .x
    };

    let total = value.chars().count();
    let (mut low, mut high) = (0usize, total);
    while low < high {
        let mid = (low + high + 1) / 2;
        if measure(mid) <= max_width {
            low = mid;
        } else {
            high = mid - 1;
        }
    }

    value.chars().take(low).chain(std::iter::once('…')).collect()
}

// Silence unused-import warnings for items kept for readability of the layout code.
#[allow(unused)]
fn _assert_imports(_: Align, _: FontSelection, _: Layout, _: RichText) {}

/// `PS_DEBUG=1` logs input events to the daemon log. Mirrors the env var `python_search/logger.py`
/// already uses.
fn debug_enabled() -> bool {
    static ENABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *ENABLED.get_or_init(|| std::env::var("PS_DEBUG").is_ok())
}
