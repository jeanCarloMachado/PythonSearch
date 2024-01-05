use druid::widget::{Flex, TextBox, Button, Controller};
use druid::{AppLauncher, LocalizedString, Widget, WidgetExt, WindowDesc, EventCtx, Event, Env};
use druid_widget_nursery::DropdownSelect;
use druid::keyboard_types::Key;
use druid::KeyEvent;


use std::env;  // Import the env module for argument parsing

use serde_json::json;

struct SaveCloseController;

struct InitialFocusController;

impl<W: Widget<Data>> Controller<Data, W> for InitialFocusController {
    fn event(&mut self, child: &mut W, ctx: &mut EventCtx, event: &Event, data: &mut Data, env: &Env) {
        if let Event::WindowConnected = event {
            ctx.request_focus();
        } else {
            child.event(ctx, event, data, env);
        }
    }
}



impl<W: Widget<Data>> Controller<Data, W> for SaveCloseController {
    fn event(&mut self, child: &mut W, ctx: &mut EventCtx, event: &Event, data: &mut Data, env: &Env) {
        match event {
            Event::KeyDown(KeyEvent { key, .. }) => {
                match key {
                    Key::Tab => {
                        data.moved_focus = true;
                    }
                    Key::Enter => {
                        // Save logic
                        if &data.moved_focus == &true {
                            let output = json!({
                                "key": &data.title,
                                "value": &data.body,
                                "type": &data.selection
                            });
                            println!("{}", output.to_string());
                            std::process::exit(0);
                        } else {

                            child.event(ctx, event, data, env);
                        }


                    }
                    Key::Escape => {
                        // Close the application
                        std::process::exit(0);
                    }
                    _ => {}
                }
            }
            _ => {}
        }
        child.event(ctx, event, data, env);
    }
}

fn build_ui() -> impl Widget<Data> {  // <--- Change the return type here
    // Create two textboxes for input.
    let body = TextBox::multiline().with_placeholder("Body").expand_width().fix_height(100.0).lens(Data::body).controller(InitialFocusController);
    let title = TextBox::new().with_placeholder("Key").expand_width().lens(Data::title);
 
    let dropdown = DropdownSelect::new(vec![
        ("Cmd".to_string(),"cmd".to_string()),
        ("CliCmd".to_string(),"cli_cmd".to_string()),
        ("File".to_string(),"file".to_string()),
        ("Snippet".to_string(),"snippet".to_string()),
        ("Url".to_string(),"url".to_string()),
    ])
    .lens(Data::selection);  // Assuming Data::selection is the field in your data model


    // Create a button which, when clicked, will print the input values as JSON.
    let button = Button::new("Save")
        .on_click(|_ctx, data: &mut Data, _env| {
            let output = json!({
                "key": &data.title,
                "value": &data.body,
                "type": &data.selection
            });
            println!("{}", output.to_string());
            std::process::exit(0);
        }).expand_width();

    // Layout widgets vertically.
    Flex::column()
        .with_child(body)
        .with_spacer(8.0)
        .with_child(title)
        .with_spacer(8.0)
        .with_child(dropdown)
        .with_spacer(8.0)
        .with_child(button)

}

#[derive(Clone, druid::Lens, druid::Data)]
struct Data {
    title: String,
    body: String,
    selection: String,  // <-- Add this line
    moved_focus: bool,
}

fn main() {

    let args: Vec<String> = env::args().collect();
    let title_default = args.get(1).unwrap_or(&"".to_string()).clone();
    let body_default = args.get(2).unwrap_or(&"".to_string()).clone();
    let selection_default = args.get(3).unwrap_or(&"snippet".to_string()).clone();


    let main_window = WindowDesc::new(build_ui().controller(SaveCloseController))  // No change needed here
        .title(LocalizedString::new("rust-gui-app-title").with_placeholder("Python Search Register new"));
    let data = Data {
        title: title_default,
        body: body_default,
        selection: selection_default, 
        moved_focus: false,
    };
    AppLauncher::with_window(main_window)
        .launch(data)  // No change needed here
        .expect("Failed to launch application");
}
