import fire

from python_search.config import ConfigurationLoader
from dataclasses import dataclass

@dataclass
class EntryData:
    key: str
    value: str


class EntryCaptureGUI:
    def launch(self, title: str = "Capture Entry", default_content: str = "", serialize_output=False) -> EntryData:
        """
        Launch the data capture GUI.
        """
        import PySimpleGUI as sg

        config = ConfigurationLoader().load_config()
        sg.theme(config.simple_gui_theme)
        font_size = config.simple_gui_font_size

        layout = [
            [sg.Text("Descriptive key name")],
            [sg.Input(key="key")],
            [sg.Text("Entry content")],
            [sg.Input(key="content", default_text=default_content)],
            [sg.Text("Type")],
            [sg.Combo(["Automatic", "Snippet",  "CliCmd", "Cmd", "URL", "File", "Anonymous"], key="type", default_value="Automatic")],
            [sg.Text("Tags")],
            [[sg.Checkbox("German", key="german", default=False)],
            [sg.Checkbox("Reminder", key="reminder", default=False)]],
            [sg.Button("Write", key="write")],
        ]

        window = sg.Window(
            title,
            layout,
            font=("Helvetica", font_size),
            alpha_channel=0.9,
            finalize=True,
        )

        # workaround for mac bug
        window.read(timeout=1000)
        window.set_alpha(1.0)

        window["key"].bind("<Return>", "_Enter")
        window["content"].bind("<Escape>", "_Esc")

        while True:
            event, values = window.read()
            if event and (event == "write" or event.endswith("_Enter")):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                break

        window.close()
        print('values', values)

        result = EntryData(values["key"], values["content"])

        if serialize_output:
            result = result.__dict__

        return result


if __name__ == "__main__":
    fire.Fire(EntryCaptureGUI().launch)