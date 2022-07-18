import fire
from python_search.config import ConfigurationLoader


def launch(default_content=""):
    """
    Launch the data capture GUI.
    """
    import PySimpleGUI as sg

    config = ConfigurationLoader().load_config()
    sg.theme(config.simple_gui_theme)
    font_size = config.simple_gui_font_size

    layout = [
        [sg.Text("Enter Description:")],
        [sg.Input(key="key")],
        [sg.Text("Content:")],
        [sg.Input(key="content", default_text=default_content)],
        [sg.Button("Write", key="write")],
    ]

    window = sg.Window(
        "Capture entry", layout, font=("Helvetica", font_size), finalize=True
    )
    window["key"].bind("<Return>", "_Enter")

    while True:
        event, values = window.read()
        if event == "write" or event.endswith("_Enter"):
            break
        if event == sg.WINDOW_CLOSED:
            break

    window.close()

    return values["key"], values["content"], "type"


if __name__ == "__main__":
    fire.Fire(launch)
