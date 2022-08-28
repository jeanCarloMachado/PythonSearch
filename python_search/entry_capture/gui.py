from dataclasses import dataclass
from typing import List

import fire

from python_search.config import ConfigurationLoader


@dataclass
class EntryData:
    """
    Entry data schema

    """

    key: str
    value: str
    type: str
    tags: List[str]


class EntryCaptureGUI:
    TAGS = [
        "German",
        "Reminder",
        "Politics",
        "Self",
        "Others",
        "Career",
        "Commitment",
        "StrategicDecision",
    ]

    def launch(
        self,
        title: str = "Capture Entry",
        default_key="",
        default_content: str = "",
        serialize_output=False,
        default_type="Snippet",
    ) -> EntryData:
        """
        Launch the data capture GUI.
        """
        import PySimpleGUI as sg

        config = ConfigurationLoader().load_config()
        sg.theme(config.simple_gui_theme)
        font_size = config.simple_gui_font_size

        content_input = sg.Input(
            key="content",
            default_text=default_content,
            expand_x=True,
            expand_y=True,
        )
        layout = [
            [sg.Text("Entry content")],
            [content_input],
            [sg.Text("Descriptive key name")],
            [
                sg.Input(
                    key="key", default_text=default_key, expand_x=True, expand_y=True
                )
            ],
            [sg.Text("Type")],
            [
                sg.Combo(
                    [
                        "Snippet",
                        "Cmd",
                        "Url",
                        "File",
                        "Anonymous",
                    ],
                    key="type",
                    default_value=default_type,
                )
            ],
            [sg.Text("Tags")],
            [sg.Checkbox(tag, key=tag, default=False) for tag in EntryCaptureGUI.TAGS],
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
        window.read(timeout=100)
        window.set_alpha(1.0)
        content_input.update(select=True)

        window["key"].bind("<Return>", "_Enter")
        window["content"].bind("<Return>", "_Enter")
        window["type"].bind("<Return>", "_Enter")
        window["key"].bind("<Escape>", "_Esc")
        window["content"].bind("<Escape>", "_Esc")
        window["type"].bind("<Escape>", "_Esc")

        while True:
            event, values = window.read()
            if event and (event == "write" or event.endswith("_Enter")):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                raise Exception("Quitting window")

        window.close()
        print("values", values)

        selected_tags = []
        for key, value in values.items():
            if key in EntryCaptureGUI.TAGS and value == True:
                selected_tags.append(key)

        result = EntryData(
            values["key"], values["content"], values["type"], selected_tags
        )

        if serialize_output:
            result = result.__dict__

        return result


if __name__ == "__main__":
    fire.Fire(EntryCaptureGUI().launch)
