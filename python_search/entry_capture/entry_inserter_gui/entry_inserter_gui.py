from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import List

import fire

from python_search.entry_capture.utils import get_page_title
from python_search.error.exception import notify_exception
from python_search.configuration.loader import ConfigurationLoader
from python_search.environment import is_mac
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.apps.notification_ui import send_notification
from python_search.entry_type.type_detector import TypeDetector


class NewEntryGUI:
    _TITLE_INPUT = "-entry-name-"
    _BODY_INPUT = "-entry-body-"
    _PREDICT_ENTRY_TITLE_READY = "-predict-entry-title-ready-"
    _PREDICT_ENTRY_TYPE_READY = "-predict-entry-type-ready-"
    _ENTRY_NAME_INPUT_SIZE = (17, 7)
    _ENTRY_BODY_INPUT_SIZE = (17, 10)

    def __init__(self, configuration=None):
        if configuration:
            self._configuration = configuration
        else:
            self._configuration = ConfigurationLoader().load_config()
        self._tags = self._configuration._default_tags
        self._prediction_uuid = None
        self._FONT = "FontAwesome" if not is_mac() else "Pragmata Pro"
        self._type_detector = TypeDetector()
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
    ) -> GuiEntryData:
        """
        Launch the entries capture GUI.
        """

        if default_content is None:
            default_content = ""

        print("Default key: ", default_key)

        self.sg.theme("Dark")
        self.sg.theme_slider_color("#000000")
        font_size = self._configuration.simple_gui_font_size

        entry_type = self.sg.Combo(
            [
                "Snippet",
                "Cmd",
                "Url",
                "File",
            ],
            key="type",
            default_value=default_type,
            button_background_color=self.sg.theme_background_color(),
            button_arrow_color=self.sg.theme_background_color(),
        )

        TAGS_PER_ROW = 6
        tags_chucks = self._chunks_of_tags(self._tags, TAGS_PER_ROW)

        key_name_input = self.sg.Input(
            key=self._TITLE_INPUT,
            default_text=default_key,
            expand_y=True,
            expand_x=True,
            size=self._ENTRY_NAME_INPUT_SIZE,
        )

        content_input = self.sg.Multiline(
            key=self._BODY_INPUT,
            default_text=default_content,
            expand_x=True,
            expand_y=True,
            no_scrollbar=True,
            size=self._ENTRY_BODY_INPUT_SIZE,
        )

        colors = ("#FFFFFF", self.sg.theme_input_background_color())
        print(colors)

        llm_component = []

        tags_block = []
        if self._tags:
            tags_block = [[self.sg.Text("Tags")], [self._checkbox_list(i) for i in tags_chucks]]


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
            tags_block,
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

        window[self._TITLE_INPUT].bind("<Escape>", "Escape")
        window[self._TITLE_INPUT].bind("<Return>", "write")
        window[self._TITLE_INPUT].bind("<Control_L><s>", "write")
        window[self._BODY_INPUT].bind("<Escape>", "Escape"),
        window["type"].bind("<Escape>", "Escape")

        self._classify_entry_type(default_key, default_content, window)

        if not default_key:
            if default_content.startswith("http"):
                self._update_title_with_url_title_thread(default_content, window)
            else:
                self._generate_title(default_content, window)


        while True:
            event, values = window.read()
            print("Event: ", event)
            if event == self.sg.WINDOW_CLOSED:
                import sys

                sys.exit(1)

            if "Escape" in event:
                import sys

                sys.exit(1)

            if event and (event == "write" or event == "-entry-name-write"):
                break

            if event == self._PREDICT_ENTRY_TYPE_READY:
                window["type"].update(values[event])
                continue

            if event == self._PREDICT_ENTRY_TITLE_READY:
                window[self._TITLE_INPUT].update(values[event])

                self._classify_entry_type(values[self._TITLE_INPUT], values[self._BODY_INPUT], window)
                continue

            if event == "-try-entry-":
                InterpreterMatcher.build_instance(
                    self._configuration
                ).get_interpreter_from_type(values["type"])(
                    values[self._BODY_INPUT]
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
            values[self._TITLE_INPUT],
            values[self._BODY_INPUT],
            values["type"],
            selected_tags,
        )

        if serialize_output:
            result = result.__dict__

        return result

    def _update_title_with_url_title_thread(self, content: str, window):
        import PySimpleGUI as sg
        window: sg.Window = window

        def _update_title(content: str, window):
            new_title = get_page_title(content)
            old_title = window[self._TITLE_INPUT]
            if old_title == new_title:
                print("Will not upgrade the title as it was already changed")
                return
            window[self._TITLE_INPUT].update(new_title)

        threading.Thread(
            target=_update_title, args=(content, window), daemon=True
        ).start()


    def _generate_title(self, content, window):
        from python_search.ps_llm.tasks.entry_title_generator import EntryTitleGenerator

        def _predict_key(window, content):
            result = EntryTitleGenerator().predict(content)
            if not result:
                return
            window.write_event_value(self._PREDICT_ENTRY_TITLE_READY, result)

        threading.Thread(
            target=_predict_key, args=(window, content), daemon=True
        ).start()

    def _classify_entry_type(self, key_content, content, window):
        if not key_content:
            key_content = ""

        def predict_entry_type(window, content):
            new_type = self._type_detector.detect(key_content, content)
            print("new_type", new_type)

            if not new_type:
                return
            window.write_event_value(self._PREDICT_ENTRY_TYPE_READY, new_type)


        threading.Thread(
            target=predict_entry_type, args=(window, content), daemon=True
        ).start()

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
