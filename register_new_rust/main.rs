use druid::widget::{Flex, TextBox, Button};
use druid::{AppLauncher, LocalizedString, Widget, WidgetExt, WindowDesc};
use serde_json::json;


fn build_ui() -> impl Widget<Data> {  // <--- Change the return type here
    // Create two textboxes for input.
    let textbox1 = TextBox::new().with_placeholder("Key").expand_width().lens(Data::input1);
    let textbox2 = TextBox::new().with_placeholder("Body").expand_width().lens(Data::input2);


    // Create a button which, when clicked, will print the input values as JSON.
    let button = Button::new("Save")
        .on_click(|_ctx, data: &mut Data, _env| {
            let output = json!({
                "key": &data.input1,
                "value": &data.input2
            });
            println!("{}", output.to_string());
            std::process::exit(0);
        }).expand_width();

    // Layout widgets vertically.
    Flex::column().with_child(textbox1).with_spacer(8.0).with_child(textbox2).with_spacer(8.0).with_child(button)

}

#[derive(Clone, druid::Lens, druid::Data)]
struct Data {
    input1: String,
    input2: String,
}

fn main() {
    let main_window = WindowDesc::new(build_ui())  // No change needed here
        .title(LocalizedString::new("rust-gui-app-title").with_placeholder("Python Search Register new"));
    let data = Data {
        input1: "".into(),
        input2: "".into(),
    };
    AppLauncher::with_window(main_window)
        .launch(data)  // No change needed here
        .expect("Failed to launch application");
}
