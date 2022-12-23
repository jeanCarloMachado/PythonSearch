from datetime import datetime

from colorama import Fore
from dateutil import parser

from python_search.config import ConfigurationLoader
from python_search.logger import setup_preview_logger
from python_search.search_ui.serialized_entry import (
    decode_serialized_data_from_entry_text,
)


class Preview:
    """
    Preview the entry in the search ui
    """

    def __init__(self):
        self.configuration = ConfigurationLoader()
        self.logger = setup_preview_logger()
        # do not send the errors to stderr, in the future we should send to kibana or a file

    def display(self, entry_text: str):
        """
        Prints the entry in the preview window

        """

        data = self._build_values_to_print(entry_text)
        self._print_values(data)

    def _print_values(self, data):
        print("")
        print(
            data["type"]
            + ": "
            + self._color_str(data["value"], self._get_color_for_type(data["type"]))
        )
        print(f"Key: {self._color_str(data['key'], Fore.YELLOW)}")
        if "description" in data:
            print(f"Description: {data['description']}")

        if "created_at" in data:
            print("Created at: " + data["created_at"])
            print("Entry Age: " + data["entry_age"])

        if "tags" in data:
            print(f"Tags: {data['tags']}")
        if "position" in data:
            print("Position: " + data["position"])

        if "uuid" in data:
            print("Uuid: " + data["uuid"][0:8])

    def _get_color_for_type(self, type):
        if type == "Cmd":
            return Fore.RED

        if type in ["Url", "File"]:
            return Fore.GREEN

        return Fore.BLUE

    def _build_values_to_print(self, entry_text) -> dict:
        key = entry_text.split(":")[0]
        # the entry content is after the key + a ":" character

        result = {}
        result["type"] = "Unknown"
        result["key"] = key
        entry_data = self._load_key_data(key)
        if "url" in entry_data:
            result["value"] = entry_data.get("url")
            result["type"] = "Url"

        if "file" in entry_data:
            result["value"] = entry_data.get("file")
            result["type"] = "File"

        if "snippet" in entry_data:
            result["value"] = entry_data.get("snippet")
            result["type"] = "Snippet"

        if "cli_cmd" in entry_data or "cmd" in entry_data:
            result["value"] = entry_data.get("cli_cmd", entry_data.get("cmd"))
            result["type"] = "Cmd"

        if "callable" in entry_data:
            value = entry_data.get("callable")
            import dill

            result["value"] = dill.source.getsource(value)

        if "created_at" in entry_data:

            creation_date = parser.parse(entry_data["created_at"])
            today = datetime.now()
            result["created_at"] = str(creation_date)
            result["entry_age"] = str(today - creation_date)

        if "description" in entry_data:
            result["description"] = entry_data["description"]

        decoded_content = decode_serialized_data_from_entry_text(
            entry_text, self.logger
        )

        if "position" in decoded_content:
            result["position"] = str(decoded_content["position"])

        result["tags"] = []
        if "tags" in entry_data:
            result["tags"] = " ".join(entry_data["tags"])

        if "tags" in decoded_content:
            result["tags"] = " ".join(decoded_content["tags"])

        if "uuid" in decoded_content:
            result["uuid"] = str(decoded_content["uuid"])

        return result

    def _color_str(self, a_string, a_color) -> str:
        return f"{a_color}{a_string}{Fore.RESET}"

    def _load_key_data(self, key):
        entries = self.configuration.load_entries()
        if not key in entries:
            print()
            print(
                (
                    f'Key "{self._color_str(key, Fore.RED)}" not found in python search data'
                )
            )
            import sys

            sys.exit(0)

        return entries[key]
