use druid::widget::{Controller, Flex, Label, List, Scroll, TextBox, WidgetExt};
use druid::{AppLauncher, Data, Env, Event, EventCtx, KeyCode, Lens, Widget, WindowDesc};
use std::sync::Arc;
use std::io::{self, BufRead};

#[derive(Clone, Data, Lens)]
struct AppState {
    filter_text: String,
    items: Arc<Vec<String>>,
    filtered_items: Arc<Vec<String>>,
    selected_index: usize, // Added field to track the highlighted line
}

fn read_input() -> Vec<String> {
    let stdin = io::stdin();
    let lines = stdin.lock().lines();
    lines.filter_map(|line| line.ok()).collect()
}

fn main() {
    let main_window = WindowDesc::new(build_ui)
        .title("Filter List")
        .window_size((400.0, 400.0));

    let initial_items = Arc::new(read_input());

    let initial_state = AppState {
        filter_text: "".into(),
        items: initial_items.clone(),
        filtered_items: initial_items,
        selected_index: 0, // Initialize the selected index
    };

    AppLauncher::with_window(main_window)
        .launch(initial_state)
        .expect("Failed to launch application");
}

fn build_ui() -> impl Widget<AppState> {
    let text_box = TextBox::new()
        .with_placeholder("Type to filter...")
        .lens(AppState::filter_text)
        .expand_width()
        .controller(InitialFocusController {})
        .controller(FilterController {});

    let list = List::new(|| {
        Label::new(|(item, selected): &(String, bool), _env: &_| {
            if *selected {
                format!("> {}", item) // Highlight the selected item
            } else {
                format!("  {}", item)
            }
        })
        .padding(10.0)
        .center()
    })
    .lens(AppState::filtered_items.map(
        // Map AppState to (item, selected) pairs
        |data: &AppState, _| {
            data.filtered_items
                .iter()
                .enumerate()
                .map(|(index, item)| (item.clone(), index == data.selected_index))
                .collect()
        },
        |data: &mut AppState, _: Vec<(String, bool)>| {}, // No-op for the setter
    ));

    let scroll = Scroll::new(list).vertical().expand();

    Flex::column().with_child(text_box).with_flex_child(scroll, 1.0)
}

struct InitialFocusController;

impl<W: Widget<AppState>> Controller<AppState, W> for InitialFocusController {
    fn event(&mut self, child: &mut W, ctx: &mut EventCtx, event: &Event, data: &mut AppState, env: &Env) {
        if let Event::WindowConnected = event {
            ctx.request_focus();
        }
        child.event(ctx, event, data, env)
    }
}

struct FilterController;

impl<W: Widget<AppState>> Controller<AppState, W> for FilterController {
    fn event(&mut self, child: &mut W, ctx: &mut EventCtx, event: &Event, data: &mut AppState, env: &Env) {
        match event {
            Event::KeyDown(key_event) => {
                match key_event.code {
                    KeyCode::ArrowDown => {
                        data.selected_index = (data.selected_index + 1).min(data.filtered_items.len().saturating_sub(1));
                    }
                    KeyCode::ArrowUp => {
                        if data.selected_index > 0 {
                            data.selected_index -= 1;
                        }
                    }
                    _ => (),
                }
                // Update filtered items on key press
                data.filtered_items = Arc::new(
                    data.items
                        .iter()
                        .filter(|item| item.to_lowercase().contains(&data.filter_text.to_lowercase()))
                        .cloned()
                        .collect(),
                );
            }
            _ => (),
        }
        child.event(ctx, event, data, env);
    }
}
