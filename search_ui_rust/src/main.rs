use druid::widget::{Flex, Label, List, Scroll, TextBox, WidgetExt};
use druid::{AppLauncher, Data, Lens, Widget, WindowDesc, Env, EventCtx, Event};
use std::sync::Arc;

#[derive(Clone, Data, Lens)]
struct AppState {
    filter_text: String,
    items: Arc<Vec<String>>,
    filtered_items: Arc<Vec<String>>,
}

fn main() {
    let main_window = WindowDesc::new(build_ui)
        .title("Filter List")
        .window_size((400.0, 400.0));

    let initial_items = Arc::new(vec![
        "Apple".into(),
        "Banana".into(),
        "Cherry".into(),
        "Date".into(),
        "Fig".into(),
        "Grape".into(),
    ]);

    let initial_state = AppState {
        filter_text: "".into(),
        items: initial_items.clone(),
        filtered_items: initial_items,
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
        .controller(FilterController {});

    let list = List::new(|| {
        Label::new(|item: &String, _env: &_| format!("{}", item))
            .padding(10.0)
            .center()
    })
    .lens(AppState::filtered_items);

    let scroll = Scroll::new(list).vertical().expand();

    Flex::column().with_child(text_box).with_flex_child(scroll, 1.0)
}

struct FilterController;

impl<W: Widget<AppState>> druid::widget::Controller<AppState, W> for FilterController {
    fn event(&mut self, child: &mut W, ctx: &mut EventCtx, event: &Event, data: &mut AppState, env: &Env) {
        match event {
            Event::KeyDown(_) => {
                // This is a simple approach that updates the filter every time a key is pressed.
                // You might want to refine this for better performance or user experience.
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
        child.event(ctx, event, data, env)
    }
}
