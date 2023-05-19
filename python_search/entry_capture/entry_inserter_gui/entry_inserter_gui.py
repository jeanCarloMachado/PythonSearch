from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import List

import fire

from python_search.error.exception import notify_exception
from python_search.chat_gpt import LLMPrompt, SUPPORTED_MODELS
from python_search.configuration.loader import ConfigurationLoader
from python_search.entry_generator import EntryGenerator
from python_search.environment import is_mac
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.sdk.web_api_sdk import PythonSearchWebAPISDK
from python_search.apps.notification_ui import send_notification
from python_search.type_detector import TypeDetector


class NewEntryGUI:
    _ENTRY_NAME_INPUT = "-entry-name-"
    _ENTRY_BODY_INPUT = "-entry-body-"
    _ENTRY_NAME_INPUT_SIZE = (17, 7)
    _ENTRY_BODY_INPUT_SIZE = (17, 10)

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()
        self._tags = self._configuration._default_tags
        self._prediction_uuid = None
        self._chat_gpt = LLMPrompt()
        self._entry_generator = EntryGenerator()
        self._FONT = "FontAwesome" if not is_mac() else "Pragmata Pro"
        import PySimpleGUI as sg

        self.sg = sg

    @notify_exception()
    def launch(
        self,
        window_title: str = "New",
        default_key: str = "",
        default_content: str = "",
        serialize_output=False,
        default_type="Snippet",
        generate_body=False,
    ) -> GuiEntryData:
        """
        Launch the entries capture GUI.
        """

        if default_content is None:
            default_content = ""

        print("Default key: ", default_key)

        config = ConfigurationLoader().load_config()
        self.sg.theme("Dark")
        self.sg.theme_slider_color("#000000")
        font_size = config.simple_gui_font_size

        entry_type = self.sg.Combo(
            [
                "Snippet",
                "Cmd",
                "Url",
                "File",
                "Anonymous",
            ],
            key="type",
            default_value=default_type,
            button_background_color=self.sg.theme_background_color(),
            button_arrow_color=self.sg.theme_background_color(),
        )

        TAGS_PER_ROW = 6
        tags_chucks = self._chunks_of_tags(self._tags, TAGS_PER_ROW)

        key_name_input = self.sg.Multiline(
            key=self._ENTRY_NAME_INPUT,
            default_text=default_key,
            expand_x=True,
            expand_y=True,
            size=self._ENTRY_NAME_INPUT_SIZE,
            no_scrollbar=True,
        )

        content_input = self.sg.Multiline(
            key=self._ENTRY_BODY_INPUT,
            default_text=default_content,
            expand_x=True,
            expand_y=True,
            no_scrollbar=True,
            size=self._ENTRY_BODY_INPUT_SIZE,
        )

        colors = ("#FFFFFF", self.sg.theme_input_background_color())
        print(colors)

        llm_component = []
        if self._configuration.is_chat_gpt_ui_enable_in_data_capture():
            llm_component = [
                self.sg.Button(
                    "Generate Body",
                    key="-generate-body-",
                    button_color=colors,
                    border_width=0,
                ),
                self.sg.Button(
                    "Generate Key",
                    key="-generate-title-",
                    button_color=colors,
                    border_width=0,
                ),
                self.sg.Combo(
                    SUPPORTED_MODELS,
                    size=(13, 1),
                    key="-model-",
                    default_value=SUPPORTED_MODELS[0],
                    button_background_color=self.sg.theme_background_color(),
                    button_arrow_color=self.sg.theme_background_color(),
                ),
                self.sg.Input(500, key="generation-size", size=(4, 1)),
            ],

        layout = [
            [self.sg.Text("Key")],
            [key_name_input],
            [self.sg.Text("Body")],
            [content_input],
            [
                self.sg.Text("Type"),
                entry_type,
                self.sg.Button(
                    "Try Entry", key="-try-entry-", button_color=colors, border_width=0
                ),
                self.sg.Push(),
            ],
            llm_component,
            [self.sg.Text("Tags")],
            [self._checkbox_list(i) for i in tags_chucks],
            [
                self.sg.Button(
                    "Write entry", key="write", button_color=colors, border_width=0
                )
            ],
        ]

        window = self.sg.Window(
            window_title,
            layout,
            font=(self._FONT, font_size),
            finalize=True,
        )

        window[self._ENTRY_NAME_INPUT].bind("<Escape>", "Escape")
        window[self._ENTRY_NAME_INPUT].bind("<Control_L><s>", "CTRL-s")
        window[self._ENTRY_NAME_INPUT].bind("<Control_L><g>", "CTRL-g")
        window[self._ENTRY_BODY_INPUT].bind("<Escape>", "Escape"),
        window["type"].bind("<Escape>", "Escape")

        self._predict_entry_type_thread(default_content, window)
        if (default_key and not default_content) or generate_body:
            self._generate_body_thread(default_key, window)

        if not default_key and default_content.startswith("http"):
            self._update_title_with_url_title_thread(default_content, window)

        while True:
            event, values = window.read()
            print("Event: ", event)
            if event == self.sg.WINDOW_CLOSED:
                import sys

                sys.exit(1)

            if "Escape" in event:
                import sys

                sys.exit(1)

            if event and (event == "write" or event == "-entry-name-CTRL-s"):
                break

            if event and (event == "-generate-body-" or event == "-entry-name-CTRL-g"):
                self._generate_body_thread(values[self._ENTRY_NAME_INPUT], window)

            if event and (event == "-generate-title-"):
                self._generate_title_thread(default_content, window)

            if event == "-type-inference-ready-":
                window["type"].update(values[event])
                continue

            if event == "-try-entry-":
                InterpreterMatcher.build_instance(
                    self._configuration
                ).get_interpreter_from_type(values["type"])(
                    values[self._ENTRY_BODY_INPUT]
                ).default()

        window.hide()
        window.close()
        logging.info("values", values)

        selected_tags = []
        if self._tags:
            for key, value in values.items():
                if key in self._tags and value is True:
                    selected_tags.append(key)

        result = GuiEntryData(
            values[self._ENTRY_NAME_INPUT],
            values[self._ENTRY_BODY_INPUT],
            values["type"],
            selected_tags,
        )

        if serialize_output:
            result = result.__dict__

        return result

    def _generate_body_thread(self, title: str, window):
        send_notification(f"Starting to generate body")

        import PySimpleGUI as sg

        window: sg.Window = window
        model = window["-model-"].get()
        print("Selected model: ", model)

        def _describe_body(title: str, window):
            body_size = window["generation-size"].get()
            description = self._entry_generator.generate_body(
                prompt=title, max_tokens=body_size, model=model
            )

            window[self._ENTRY_BODY_INPUT].update(description)

        threading.Thread(
            target=_describe_body, args=(title, window), daemon=True
        ).start()

    def _get_page_title(self, url):
        import subprocess

        cmd = f"""curl -f -L {url} | python -c 'import sys, re; result = re.findall("<title>(.*?)</title>", str(sys.stdin.read()));  print(result[0])'"""
        from subprocess import PIPE, Popen

        with Popen(cmd, stdout=PIPE, stderr=None, shell=True) as process:
            output = process.communicate()[0].decode("utf-8")
        if not process.returncode == 0:
            return ""
        return output

    def _update_title_with_url_title_thread(self, content: str, window):
        send_notification(f"Starting to get url title")
        self._chat_gpt = LLMPrompt(window["generation-size"].get())
        import PySimpleGUI as sg

        window: sg.Window = window

        def _update_title(content: str, window):
            new_title = self._get_page_title(content)
            old_title = window[self._ENTRY_NAME_INPUT]
            if old_title == new_title:
                print("Will not upgrade the title as it was already changed")
                return
            window[self._ENTRY_NAME_INPUT].update(new_title)

        threading.Thread(
            target=_update_title, args=(content, window), daemon=True
        ).start()

    def _generate_title_thread(self, content: str, window):
        send_notification(f"Starting to generate title")
        self._chat_gpt = LLMPrompt(window["generation-size"].get())
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
        new_type = TypeDetector().detect("", content)

        if not new_type:
            return

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
        return ([self.sg.Checkbox(tag, key=tag, default=False) for tag in tags],)

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
    fire.Fire(NewEntryGUI().launch_prompt)


if __name__ == "__main__":
    fire.Fire(NewEntryGUI().launch)
