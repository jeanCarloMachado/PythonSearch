from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import List

import fire

from python_search.chat_gpt import ChatGPT
from python_search.configuration.loader import ConfigurationLoader
from python_search.entry_type.classifier_inference import ClassifierInferenceClient
from python_search.infrastructure.arize import Arize
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.sdk.web_api_sdk import PythonSearchWebAPISDK


class EntryCaptureGUI:
    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()
        self._tags = self._configuration._default_tags
        self._prediction_uuid = None

    def launch(
        self,
        title: str = "New Entry",
        default_key: str = "",
        default_content: str = "",
        serialize_output=False,
        default_type="Snippet",
    ) -> GuiEntryData:
        """
        Launch the _entries capture GUI.
        """

        print("Default key: ", default_key)
        import PySimpleGUI as sg

        self._sg = sg

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

        if not default_key:
            default_key = self.genearte_key_from_content(default_content)

        key_name_input = sg.Input(
            key="key", default_text=default_key, expand_x=True, expand_y=True,
            size=(15, 1),
        )


        content_input = sg.Multiline(
            key="content",
            default_text=default_content,
            expand_x=True,
            expand_y=True,
            no_scrollbar=False,
            size=(15, 7),
        )
        layout = [
            [sg.Text("Key name")],
            [
                key_name_input
            ],
            [sg.Text("Entry content")],
            [content_input],
            [sg.Text("Generator"), sg.Button("Content", key="-generate-body-"), sg.Button("Title", key="-generate-title-")],
            [sg.Text("Type")],
            [entry_type, sg.Button("Try it", key="-try-entry-")],
            [sg.Text("Tags")],
            [self._checkbox_list(i) for i in tags_chucks],
            [sg.Button("Write", key="write")],
        ]

        window = sg.Window(
            title,
            layout,
            font=("Helvetica", font_size),
            finalize=True,
        )

        # workaround for mac bug


        window["key"].bind("<Return>", "_Enter")
        window["content"].bind("<Return>", "_Enter")
        window["type"].bind("<Return>", "_Enter")
        window["key"].bind("<Escape>", "_Esc")
        window["content"].bind("<Escape>", "_Esc")
        window["type"].bind("<Escape>", "_Esc")

        threading.Thread(
            target=self._predict_entry_type, args=(window, default_content), daemon=True
        ).start()

        while True:
            event, values = window.read()
            if event and (event == "-generate-body-"):
                window['content'].update(ChatGPT().answer(values['key']))

            if event and (event == "-generate-title-"):
                window['key'].update(self.genearte_key_from_content(values['content']))

            if event and (event == "write" or event.endswith("_Enter")):
                break

            if event == "-type-inference-ready-":
                window["type"].update(values[event])
                continue

            if event == "-try-entry-":
               InterpreterMatcher.build_instance(self._configuration).get_interpreter_from_type(values['type'])(values['content']).default()

            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                raise Exception("Quitting window")

        window.hide()
        window.close()
        logging.info("values", values)

        selected_tags = []
        for key, value in values.items():
            if key in self._tags and value == True:
                selected_tags.append(key)

        result = GuiEntryData(
            values["key"], values["content"], values["type"], selected_tags
        )

        #self._report_actual(result)

        if serialize_output:
            result = result.__dict__

        return result

    def genearte_key_from_content(self, content: str) -> str:
        return ChatGPT().answer("generate a description in the imperative form with most 5 words of the follwing text: " + content)

    def _report_actual(self, data: GuiEntryData):
        if not self._prediction_uuid:
            print("No prediction uuid, skipping report")
            return

        if not Arize.is_installed():
            return
        arize_client = Arize().get_client()

        from arize.utils.types import Environments, ModelTypes

        data = {
            "model_id": Arize.MODEL_ID,
            "model_version": Arize.MODEL_VERSION,
            "model_type": ModelTypes.SCORE_CATEGORICAL,
            "environment": Environments.PRODUCTION,
            "prediction_id": self._prediction_uuid,
            "actual_label": data.type,
        }
        print(f"Data to send arize: {data}")

        arize_result = arize_client.log(**data)
        Arize.arize_responses_helper(arize_result)

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
        return ([self._sg.Checkbox(tag, key=tag, default=False) for tag in tags],)

    def _chunks_of_tags(self, lst, n):
        """Yield successive n-sized chunks from lst."""
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


if __name__ == "__main__":
    fire.Fire(EntryCaptureGUI().launch)
