from __future__ import annotations


import fire

from python_search.apps.notification_ui import send_notification
from python_search.entry_capture.entry_inserter_gui.entry_gui_data import GuiEntryData
from python_search.entry_capture.filesystem_entry_inserter import (
    FilesystemEntryInserter,
)
from python_search.error.exception import notify_exception
from python_search.configuration.loader import ConfigurationLoader
from python_search.environment import is_mac
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.entry_type.type_detector import TypeDetector
from python_search.entry_type.entity import infer_default_type
from python_search.interpreter.base import BaseInterpreter
from python_search.apps.clipboard import Clipboard


class NewEntryGUI:
    _TITLE_INPUT = "-entry-name-"
    _BODY_INPUT = "-entry-body-"
    _PREDICT_ENTRY_TITLE_READY = "-predict-entry-title-ready-"
    _PREDICT_ENTRY_TYPE_READY = "-predict-entry-type-ready-"
    _ENTRY_NAME_INPUT_SIZE = (17, 7)
    _ENTRY_BODY_INPUT_SIZE = (17, 10)
    _WINDOW_SIZE = (600, 400)

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
    def launch_loop(self, default_type=None, default_key="", default_content=""):
        """
        Create a new inferred entry based on the clipboard content
        """

        if not default_content:
            default_content = Clipboard().get_content()

        if not default_type:
            default_type = infer_default_type(default_content)

        self.launch(
            "New Entry",
            default_content=default_content,
            default_key=default_key,
            default_type=default_type,
        )

    def _save_entry_data(self, entry_data: GuiEntryData):
        send_notification(f"Creating new entry")
        key = self._sanitize_key(entry_data.key)
        interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
            self._configuration
        ).get_interpreter_from_type(entry_data.type)

        dict_entry = interpreter(entry_data.value).to_dict()
        if entry_data.tags:
            dict_entry["tags"] = entry_data.tags

        entry_inserter = FilesystemEntryInserter(self._configuration)
        entry_inserter.insert(key, dict_entry)

    @notify_exception()
    def launch(
        self,
        window_title: str = "New",
        default_key: str = "",
        default_content: str = "",
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

        tags_block = []
        if self._tags:
            tags_block = [
                [self.sg.Text("Tags")],
                [self._checkbox_list(i) for i in tags_chucks],
            ]

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
            tags_block,
            [
                self.sg.Button(
                    "Write entry", key="write", button_color=colors, border_width=0
                ),
                self.sg.Button(
                    "Refresh", key="refresh", button_color=colors, border_width=0
                ),
            ],
        ]

        window = self.sg.Window(
            window_title,
            layout,
            font=(self._FONT, font_size),
            finalize=True,
            size=self._WINDOW_SIZE,
        )

        window.set_title("Register New")

        window[self._TITLE_INPUT].bind("<Escape>", "Escape")
        window[self._TITLE_INPUT].bind("<Return>", "write")
        window[self._TITLE_INPUT].bind("<Control_L><s>", "write")
        window[self._TITLE_INPUT].bind("<Control_L><r>", "refresh")
        window[self._BODY_INPUT].bind("<Control_L><r>", "refresh")
        window[self._BODY_INPUT].bind("<Escape>", "Escape"),
        window["type"].bind("<Escape>", "Escape")

        try:
            while True:
                event, values = window.read()
                print("Event: ", event)
                if event == self.sg.WINDOW_CLOSED:
                    import sys

                    sys.exit(1)

                if "Escape" in event:
                    print("Hiding window")
                    from python_search.host_system.window_hide import HideWindow

                    HideWindow().hide()

                if event and event == "refresh" or "refresh" in event:
                    new_content = Clipboard().get_content()
                    window[self._BODY_INPUT].update(new_content)
                    self._classify_entry_type(default_key, new_content, window)
                    continue

                if event == self._PREDICT_ENTRY_TYPE_READY:
                    window["type"].update(values[event])
                    continue

                if event == self._PREDICT_ENTRY_TITLE_READY:
                    window[self._TITLE_INPUT].update(values[event])

                    self._classify_entry_type(
                        values[self._TITLE_INPUT], values[self._BODY_INPUT], window
                    )
                    continue

                if event == "-try-entry-":
                    InterpreterMatcher.build_instance(
                        self._configuration
                    ).get_interpreter_from_type(values["type"])(
                        values[self._BODY_INPUT]
                    ).default()

                if event and (event == "write" or event == "-entry-name-write"):
                    selected_tags = []
                    if self._tags:
                        for key, value in values.items():
                            if key in self._tags and value is True:
                                selected_tags.append(key)

                        entry_data = GuiEntryData(
                            values[self._TITLE_INPUT],
                            values[self._BODY_INPUT],
                            values["type"],
                            selected_tags,
                        )

                    window[self._BODY_INPUT].update("")
                    window[self._TITLE_INPUT].update("")
                    try:
                        self._save_entry_data(entry_data)
                    except:
                        notify_exception()

                    continue

        except:
            notify_exception()

    def _sanitize_key(self, key):
        return key.replace("\n", " ").replace(":", " ").strip()

    def _classify_entry_type(self, key_content, content, window):
        if not key_content:
            key_content = ""

        new_type = self._type_detector.detect(key_content, content)
        print("new_type", new_type)

        if not new_type:
            return
        window.write_event_value(self._PREDICT_ENTRY_TYPE_READY, new_type)

    def _checkbox_list(self, tags):
        return ([self.sg.Checkbox(tag, key=tag, default=False) for tag in tags],)

    def _chunks_of_tags(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        if not lst:
            return []
        for i in range(0, len(lst), n):
            yield lst[i : i + n]


def main():
    fire.Fire(NewEntryGUI().launch)


def launch_ui():
    main()


if __name__ == "__main__":
    main()
