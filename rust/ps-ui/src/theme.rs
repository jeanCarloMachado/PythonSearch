use egui::{Color32, CornerRadius, FontData, FontDefinitions, FontFamily, FontId, TextStyle};

/// Named text roles used by the launcher. egui's default styles do not map onto a search panel,
/// so the whole scale is defined here.
pub mod text {
    pub const QUERY: &str = "query";
    pub const KEY: &str = "key";
    pub const CONTENT: &str = "content";
    pub const CHIP: &str = "chip";
    pub const HINT: &str = "hint";
}

pub struct Palette {
    pub text: Color32,
    pub text_dim: Color32,
    pub text_faint: Color32,
    pub accent: Color32,
    pub selection: Color32,
    /// Selection fill when the panel does not hold keyboard focus. macOS greys out selection in
    /// inactive windows; without it there is no way to tell that typing will go somewhere else.
    pub selection_inactive: Color32,
    pub separator: Color32,
    pub chip_bg: Color32,
    /// Query text drawn on top of the selection fill.
    pub selected_text: Color32,
    /// The panel's own background. Near-opaque: the vibrancy backdrop alone leaves the content
    /// area see-through, which makes entry text unreadable over a busy desktop.
    pub panel_bg: Color32,
}

impl Palette {
    pub fn dark() -> Self {
        Palette {
            text: Color32::from_rgb(0xF2, 0xF2, 0xF7),
            text_dim: Color32::from_rgb(0x9A, 0x9A, 0xA4),
            text_faint: Color32::from_rgb(0x6E, 0x6E, 0x78),
            accent: Color32::from_rgb(0x0A, 0x84, 0xFF),
            selection: Color32::from_rgba_unmultiplied(0x0A, 0x84, 0xFF, 0xD0),
            selection_inactive: Color32::from_rgba_unmultiplied(0x7A, 0x7A, 0x82, 0x8A),
            separator: Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0x18),
            chip_bg: Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0x1A),
            selected_text: Color32::WHITE,
            panel_bg: Color32::from_rgba_unmultiplied(0x1E, 0x1E, 0x20, 0xFA),
        }
    }

    pub fn light() -> Self {
        Palette {
            text: Color32::from_rgb(0x1C, 0x1C, 0x1E),
            text_dim: Color32::from_rgb(0x6E, 0x6E, 0x73),
            text_faint: Color32::from_rgb(0x9A, 0x9A, 0xA0),
            accent: Color32::from_rgb(0x00, 0x7A, 0xFF),
            selection: Color32::from_rgba_unmultiplied(0x00, 0x7A, 0xFF, 0xE0),
            selection_inactive: Color32::from_rgba_unmultiplied(0xB0, 0xB0, 0xB8, 0xC0),
            separator: Color32::from_rgba_unmultiplied(0x00, 0x00, 0x00, 0x14),
            chip_bg: Color32::from_rgba_unmultiplied(0x00, 0x00, 0x00, 0x0E),
            selected_text: Color32::WHITE,
            panel_bg: Color32::from_rgba_unmultiplied(0xF7, 0xF7, 0xF9, 0xFA),
        }
    }

    /// Selection fill for the current focus state.
    pub fn selection_for(&self, focused: bool) -> Color32 {
        if focused {
            self.selection
        } else {
            self.selection_inactive
        }
    }

    /// Text colour for a row's content column, selected rows excepted.
    pub fn content_on(&self, selected: bool) -> Color32 {
        if selected {
            Color32::from_rgba_unmultiplied(0xFF, 0xFF, 0xFF, 0xC8)
        } else {
            self.text_dim
        }
    }

    pub fn key_on(&self, selected: bool) -> Color32 {
        if selected {
            Color32::WHITE
        } else {
            self.text
        }
    }
}

/// Window and row geometry, in points. Kept together so the daemon can compute the window height
/// without duplicating the layout constants the painter uses.
pub struct Metrics;

impl Metrics {
    pub const WINDOW_WIDTH: f32 = 720.0;
    pub const QUERY_ROW_HEIGHT: f32 = 68.0;
    pub const ROW_HEIGHT: f32 = 46.0;
    pub const HINT_ROW_HEIGHT: f32 = 30.0;
    pub const SIDE_PADDING: f32 = 22.0;
    pub const CORNER_RADIUS: f32 = 14.0;
    pub const MAX_VISIBLE_ROWS: usize = 8;

    /// Total window height for a given number of visible rows.
    pub fn window_height(visible_rows: usize) -> f32 {
        if visible_rows == 0 {
            return Self::QUERY_ROW_HEIGHT;
        }
        Self::QUERY_ROW_HEIGHT
            + visible_rows as f32 * Self::ROW_HEIGHT
            + Self::HINT_ROW_HEIGHT
            + 8.0
    }
}

/// Local hour at which the panel switches to the light palette.
const LIGHT_FROM_HOUR: u8 = 7;
/// Local hour at which it switches back to dark.
const DARK_FROM_HOUR: u8 = 19;

/// Whether to render dark right now.
///
/// Driven by the time of day rather than the system appearance, so the panel is dark at night even
/// when macOS is left in light mode. `PS_UI_THEME` overrides it: `dark`, `light`, or `system` to
/// follow macOS instead.
pub fn dark_mode_now() -> bool {
    match std::env::var("PS_UI_THEME").as_deref() {
        Ok("dark") => return true,
        Ok("light") => return false,
        Ok("system") => return ps_mac::is_dark_mode(),
        _ => {}
    }

    let hour = ps_mac::local_hour();
    !(LIGHT_FROM_HOUR..DARK_FROM_HOUR).contains(&hour)
}

pub fn install(ctx: &egui::Context) {
    let mut fonts = FontDefinitions::default();
    fonts.font_data.insert(
        "inter".into(),
        std::sync::Arc::new(FontData::from_static(include_bytes!(
            "../../assets/Inter-Regular.ttf"
        ))),
    );
    fonts.font_data.insert(
        "inter-medium".into(),
        std::sync::Arc::new(FontData::from_static(include_bytes!(
            "../../assets/Inter-Medium.ttf"
        ))),
    );
    fonts.font_data.insert(
        "inter-display".into(),
        std::sync::Arc::new(FontData::from_static(include_bytes!(
            "../../assets/InterDisplay-Medium.ttf"
        ))),
    );

    fonts
        .families
        .entry(FontFamily::Proportional)
        .or_default()
        .insert(0, "inter".into());
    fonts
        .families
        .insert(FontFamily::Name("medium".into()), vec!["inter-medium".into()]);
    fonts.families.insert(
        FontFamily::Name("display".into()),
        vec!["inter-display".into()],
    );

    ctx.set_fonts(fonts);

    let text_styles: std::collections::BTreeMap<TextStyle, FontId> = [
        (
            TextStyle::Name(text::QUERY.into()),
            FontId::new(25.0, FontFamily::Name("display".into())),
        ),
        (
            TextStyle::Name(text::KEY.into()),
            FontId::new(15.0, FontFamily::Name("medium".into())),
        ),
        (
            TextStyle::Name(text::CONTENT.into()),
            FontId::new(13.0, FontFamily::Proportional),
        ),
        (
            TextStyle::Name(text::CHIP.into()),
            FontId::new(10.0, FontFamily::Name("medium".into())),
        ),
        (
            TextStyle::Name(text::HINT.into()),
            FontId::new(11.0, FontFamily::Proportional),
        ),
        (TextStyle::Body, FontId::new(14.0, FontFamily::Proportional)),
    ]
    .into();

    ctx.all_styles_mut(|style| {
        style.text_styles = text_styles.clone();
        style.visuals.window_corner_radius = CornerRadius::same(Metrics::CORNER_RADIUS as u8);
        style.visuals.panel_fill = Color32::TRANSPARENT;
        style.visuals.window_fill = Color32::TRANSPARENT;
        style.spacing.item_spacing = egui::vec2(0.0, 0.0);
    });
}
