import fire

from python_search.config import ConfigurationLoader


class EntryCaptureGUI:
    def launch(self, title="Capture Entry", default_content=""):
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
            if event == "write" or event.endswith("_Enter"):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                break

        window.close()

        return values["key"], values["content"], "type"


if __name__ == "__main__":
    fire.Fire(EntryCaptureGUI().launch)
