from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import List

import fire
import PySimpleGUI as sg

from python_search.chat_gpt import ChatGPT
from python_search.configuration.loader import ConfigurationLoader
from python_search.entry_type.classifier_inference import ClassifierInferenceClient
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.sdk.web_api_sdk import PythonSearchWebAPISDK
from python_search.apps.notification_ui import send_notification


class EntryCaptureGUI:
    _ENTRY_NAME_INPUT = "-entry-name-"
    _ENTRY_BODY_INPUT = "-entry-body-"

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()
        self._tags = self._configuration._default_tags
        self._prediction_uuid = None
        self._chat_gpt = ChatGPT()

    def launch_prompt(
        self,
        description: str = "",
        content: str = "",
        description_with_clipboard=False,
    ) -> GuiEntryData:
        generate_body = False
        if description_with_clipboard:
            generate_body = True
            from python_search.apps.clipboard import Clipboard

            clipboard_content = Clipboard().get_content()
            description = description + clipboard_content

        return self.launch(
            default_key=description,
            default_content=content,
            generate_body=generate_body,
        )

    def launch(
        self,
        window_title: str = "New",
        default_key: str = "",
        default_content: str = "",
        serialize_output=False,
        default_type="Snippet",
    ) -> GuiEntryData:
        """
        Launch the _entries capture GUI.
        """

        if default_content is None:
            default_content = ""

        print("Default key: ", default_key)


        config = ConfigurationLoader().load_config()
        sg.theme(config.simple_gui_theme)
        font_size = config.simple_gui_font_size


        entry_type = sg.Combo(
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

        tags_chucks = self._chunks_of_tags(self._tags, 4)

        key_name_input = sg.Multiline(
            key=self._ENTRY_NAME_INPUT,
            default_text=default_key,
            expand_x=True,
            expand_y=True,
            size=(15, 5),
        )

        content_input = sg.Multiline(
            key=self._ENTRY_BODY_INPUT,
            default_text=default_content,
            expand_x=True,
            expand_y=True,
            no_scrollbar=False,
            size=(15, 7),
        )
        layout = [
            [sg.Text("Description")],
            [key_name_input],
            [sg.Text("Body")],
            [content_input],
            [
                sg.Text("Generator"),
                sg.Button("Body", key="-generate-body-"),
                sg.Button("Description", key="-generate-title-"),
                sg.Text("Response Size"),
                sg.Input(500, key="generation-size", expand_x=False),
            ],
            [sg.Text("Type")],
            [entry_type, sg.Button("Try it", key="-try-entry-")],
            [sg.Text("Tags")],
            [self._checkbox_list(i) for i in tags_chucks],
            [sg.Button("Write entry", key="write")],
        ]

        window = sg.Window(
            window_title,
            layout,
            font=("Helvetica", font_size),
            finalize=True,
        )


        window[self._ENTRY_NAME_INPUT].bind("<Escape>", "Escape")
        window[self._ENTRY_BODY_INPUT].bind("<Escape>", "Escape"),
        window["type"].bind("<Escape>", "_Esc")

        self._predict_entry_type_thread(default_content, window)
        if default_key:
            self._generate_body_thread(default_key, window)
        while True:
            event, values = window.read()
            if event == sg.WINDOW_CLOSED:
                raise Exception("Window closed")

            if "Escape" in event:
                raise Exception("Window closed")

            if event and (event == "-generate-body-"):
                self._generate_body_thread(values[self._ENTRY_NAME_INPUT], window)

            if event and (event == "-generate-title-"):
                self._generate_title_thread(default_content, window)

            if event and event == "write":
                break

            if event == "-type-inference-ready-":
                window["type"].update(values[event])
                continue

            if event == "-try-entry-":
                InterpreterMatcher.build_instance(
                    self._configuration
                ).get_interpreter_from_type(values["type"])(values[self._ENTRY_BODY_INPUT]).default()


        window.hide()
        window.close()
        logging.info("values", values)

        selected_tags = []
        if self._tags:
            for key, value in values.items():
                if key in self._tags and value is True:
                    selected_tags.append(key)

        result = GuiEntryData(
            values[self._ENTRY_NAME_INPUT], values[self._ENTRY_BODY_INPUT], values["type"], selected_tags
        )

        if serialize_output:
            result = result.__dict__

        return result


    def _generate_body_thread(self, title: str, window):

        send_notification(f"Starting to generate body")

        self._chat_gpt = ChatGPT(window["generation-size"].get())

        window: sg.Window = window

        def _describe_body(title: str, window):
            description = self._chat_gpt.answer(title)
            window[self._ENTRY_BODY_INPUT].update(description)

        threading.Thread(
            target=_describe_body, args=(title, window), daemon=True
        ).start()

    def _generate_title_thread(self, content: str, window):
        send_notification(f"Starting to generate title")
        self._chat_gpt = ChatGPT(window["generation-size"].get())
        import PySimpleGUI as sg

        window: sg.Window = window
        old_title = window[self._ENTRY_NAME_INPUT]

        def _describe_body(content: str, window):
            description = self.genearte_key_from_content(content)
            new_title = window[self._ENTRY_NAME_INPUT]
            if old_title != new_title:
                print("Will not upgrade the title as it was already changed")
                return
            window[self._ENTRY_NAME_INPUT].update(description)

        threading.Thread(
            target=_describe_body, args=(content, window), daemon=True
        ).start()

    def genearte_key_from_content(self, content: str) -> str:
        return self._chat_gpt.answer(
            "generate a description in the imperative form with most 5 words of the follwing text: "
            + content
        )


    def _predict_entry_type_thread(self, content, window):
        threading.Thread(
            target=self._predict_entry_type, args=(window, content), daemon=True
        ).start()

    def _predict_entry_type(self, window, content):
        result = ClassifierInferenceClient().predict_from_content(content)

        if not result:
            return

        new_type = result[0]
        self._prediction_uuid = result[1]
        print(f"New type: {new_type}, uuid: {self._prediction_uuid}")
        window.write_event_value("-type-inference-ready-", new_type)

    def _generate_description(self, window, content):
        result = PythonSearchWebAPISDK().generate_description(
            {"content": content, "temperature": 0.2}
        )

        if not result:
            return

        description = result["generated_description"]
        print(f"New description: {description}")
        window.write_event_value("-generated-key-ready-", description)

    def _checkbox_list(self, tags):
        return ([sg.Checkbox(tag, key=tag, default=False) for tag in tags],)

    def _chunks_of_tags(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        if not lst:
            return []
        for i in range(0, len(lst), n):
            yield lst[i : i + n]


@dataclass
class GuiEntryData:
    """
    Entry _entries schema

    """

    key: str
    value: str
    type: str
    tags: List[str]


def main():
    fire.Fire(EntryCaptureGUI().launch_prompt)


if __name__ == "__main__":
    fire.Fire(EntryCaptureGUI().launch)
