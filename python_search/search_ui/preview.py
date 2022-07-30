from datetime import datetime


class Preview:
    def display(self, entry_text):
        """
        Prints the entry in the preview window
        """
        key = entry_text.split(":")[0]
        from colorama import Fore, Style

        try:

            from python_search.ranking.entries_loader import EntriesLoader

            entry_data = EntriesLoader.load_all_entries()[key]

            if "url" in entry_data:
                print("Type: URL")
                print(f"{Fore.BLUE}{entry_data['url']}{Style.RESET_ALL}")
                del entry_data["url"]

            if "snippet" in entry_data:
                print("Type: Snippet")
                print(f"{Fore.YELLOW}{entry_data['snippet']}{Style.RESET_ALL}")
                del entry_data["snippet"]

            if "cmd" in entry_data:
                print("Type: Cmd")
                print(f"{Fore.GREEN}{entry_data['cmd']}{Style.RESET_ALL}")
                del entry_data["cmd"]

            if "cli_cmd" in entry_data:
                print("Type: CliCmd")
                print(f"{Fore.GREEN}{entry_data['cli_cmd']}{Style.RESET_ALL}")
                del entry_data["cli_cmd"]

            print("")

            for key, value in entry_data.items():
                print(f"{key}: {value}")

            if "created_at" in entry_data:
                from dateutil import parser

                creation_date = parser.parse(entry_data["created_at"])
                today = datetime.now()
                print(f"Entry age: {today - creation_date}")

        except BaseException as e:
            print(entry_text)
            print(f"""Error while decoding: {e}""")
            raise e
