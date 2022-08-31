import json
import logging
from datetime import datetime

from colorama import Fore, Style

from python_search.config import ConfigurationLoader


class Preview:
    """
    Preview the entry in the search ui
    """

    def __init__(self):
        self.configuration = ConfigurationLoader()
        self.logger = logging.getLogger("preview_entry")
        # do not send the errors to stderr, in the future we should send to kibana or a file
        self.logger.propagate = False

    def display(self, entry_text: str):
        """
        Prints the entry in the preview window
        """
        data = entry_text.split(":")
        key = data[0]
        # the entry content is after the key + a ":" character
        serialized_content = entry_text[len(key) + 1 :]
        type = "Unknown"

        try:

            entry_data = self.configuration.load_entries()[key]
            print("")
            if "url" in entry_data or "file" in entry_data:

                value = entry_data.get("url", entry_data.get("file"))

                print(f"{Fore.GREEN}{value}{Style.RESET_ALL}")
                if "url" in entry_data:
                    del entry_data["url"]

                if "file" in entry_data:
                    del entry_data["file"]
                type = "UrlInterpreter" if "url" in entry_data else "File"

            if "snippet" in entry_data:
                print(f"{Fore.BLUE}{entry_data['snippet']}{Style.RESET_ALL}")
                del entry_data["snippet"]
                type = "Snippet"

            if "cli_cmd" in entry_data or "cmd" in entry_data:
                value = entry_data.get("cli_cmd", entry_data.get("cmd"))
                print(f"{Fore.RED}{value}{Style.RESET_ALL}")
                type = "Cmd" if "cmd" in entry_data else "CliCmd"

                if "cli_md" in entry_data:
                    del entry_data["cli_cmd"]

                if "cmd" in entry_data:
                    del entry_data["cmd"]

            if "callable" in entry_data:
                value = entry_data.get("callable")
                import dill

                print(f"{Fore.RED}{dill.source.getsource(value)}{Style.RESET_ALL}")
                type = "Callable"
                if "callable" in entry_data:
                    del entry_data["callable"]

            print("")

            print(f"key: {Fore.YELLOW}{key}{Style.RESET_ALL}")
            print("type: " + type)

            for key, value in entry_data.items():
                print(f"{key}: {value}")

            if "created_at" in entry_data:
                from dateutil import parser

                creation_date = parser.parse(entry_data["created_at"])
                today = datetime.now()
                print(f"entry age: {today - creation_date}")

            try:
                decoded_content = json.loads(serialized_content)
                print(f"position: {decoded_content['position']}")
            except Exception as e:
                self.logger.error(str(e))
                pass

        except BaseException as e:
            print(e)
            self.logger.error(str(e))
