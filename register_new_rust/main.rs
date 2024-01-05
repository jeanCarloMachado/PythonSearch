use druid::widget::{Flex, TextBox, Button};
use druid::{AppLauncher, LocalizedString, Widget, WidgetExt, WindowDesc};
use druid_widget_nursery::DropdownSelect;

use std::env;  // Import the env module for argument parsing

use serde_json::json;


fn build_ui() -> impl Widget<Data> {  // <--- Change the return type here
    // Create two textboxes for input.
    let textbox1 = TextBox::new().with_placeholder("Key").expand_width().lens(Data::title);
    let body = TextBox::new().with_placeholder("Body").expand_width().fix_height(100.0).lens(Data::body);
 
    let dropdown = DropdownSelect::new(vec![
        ("CliCmd".to_string(),"cmd".to_string()),
        ("Snippet".to_string(),"snippet".to_string()),
        ("Url".to_string(),"url".to_string()),
    ])
    .lens(Data::selection);  // Assuming Data::selection is the field in your data model


    // Create a button which, when clicked, will print the input values as JSON.
    let button = Button::new("Save")
        .on_click(|_ctx, data: &mut Data, _env| {
            let output = json!({
                "key": &data.title,
                "body": &data.body,
                "type": &data.selection
            });
            println!("{}", output.to_string());
            std::process::exit(0);
        }).expand_width();

    // Layout widgets vertically.
    Flex::column()
        .with_child(textbox1)
        .with_spacer(8.0)
        .with_child(body)
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
}

fn main() {

    let args: Vec<String> = env::args().collect();
    let title_default = args.get(1).unwrap_or(&"".to_string()).clone();
    let body_default = args.get(2).unwrap_or(&"".to_string()).clone();
    let selection_default = args.get(3).unwrap_or(&"snippet".to_string()).clone();


    let main_window = WindowDesc::new(build_ui())  // No change needed here
        .title(LocalizedString::new("rust-gui-app-title").with_placeholder("Python Search Register new"));
    let data = Data {
        title: title_default,
        body: body_default,
        selection: selection_default, 
    };
    AppLauncher::with_window(main_window)
        .launch(data)  // No change needed here
        .expect("Failed to launch application");
}
