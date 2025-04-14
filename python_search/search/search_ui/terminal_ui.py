import asyncio
import os
import sys
from typing import Any
import json
import time

from python_search.core_entities import Entry
from python_search.search.search_ui.QueryLogic import QueryLogic
from python_search.search.search_ui.search_actions import Actions
from python_search.search.search_ui.search_utils import setup_datadog

from python_search.apps.theme.theme import get_current_theme
from python_search.host_system.system_paths import SystemPaths
from python_search.logger import setup_term_ui_logger

logger = setup_term_ui_logger()
from getch import getch

startup_time = time.time_ns()
statsd = setup_datadog()

# disable hugging face warning about forking token paralelism when reloading entries
os.environ["TOKENIZERS_PARALLELISM"] = 'false'
class SearchTerminalUi:
    MAX_KEY_SIZE = 35
    MAX_CONTENT_SIZE = 46
    RUN_KEY_EVENT = "python_search_run_key"

    _documents_future = None
    commands = None
    documents = None

    def __init__(self) -> None:
        self.theme = get_current_theme()
        self.cf = self.theme.get_colorful()
        self.actions = Actions()
        self.previous_query = ""
        self.typed_up_to_run = ""
        self.tdw = None
        self.reloaded = False
        self.first_run = True

        self._setup_entries()
        self.normal_mode = False

    def run(self):
        """
        Rrun the application main loop
        """
        statsd.increment("ps_run_triggered")
        # hide cursor
        print("\033[?25l", end="")
        self.query = ""
        self.selected_row = 0
        self.selected_query = -1
        end_startup = time.time_ns()
        duration_startup_seconds = (end_startup - startup_time) / 1000**3
        statsd.histogram("ps_startup_no_render_seconds", duration_startup_seconds)

        self.render()
        self.first_run = False

        while True:
            # blocking function call
            c = self.get_caracter()
            logger.info("processing char" + c)
            self.process_chars(c)
            self.render()
            # sets query here
            self.previous_query = self.query

    @statsd.timed("ps_render")
    def render(self):
        self.print_first_line()
        logger.info("rendering loop started")
        current_key = 0
        self.matched_keys = []

        for key in self.search_logic.search(self.query):
            try:
                entry = Entry(key, self.commands[key])
            except Exception:
                entry = Entry(key, {"snippet": "Error loading entry"})

            if current_key == self.selected_row:
                self.print_highlighted(key, entry)
            else:
                self.print_normal_row(key, entry)

            current_key += 1
            self.matched_keys.append(key)
        
    def _setup_entries(self):
        import subprocess

        output = subprocess.getoutput(
            SystemPaths.BINARIES_PATH + "/pys _entries_loader load_entries_as_json 2>/dev/null"
        )
        #print("output", output)
        self.commands = json.loads(output)
        self.search_logic = QueryLogic(self.commands)


    def get_caracter(self) -> str:
        try:

            logger.info("getting char")
            c = getch()
            return c
        except Exception:
            return " "

    def print_first_line(self):
        if self.normal_mode:
            content = self.cf.query_enabled("* " + self.query)
        else:
            content = self.cf.query(self.query)

        print(
            "\x1b[2J\x1b[H"
            + self.cf.cursor(f"({len(self.commands)})> ")
            + f"{self.cf.bold(content)}"
        )

    def process_chars(self, c: str):
        self.typed_up_to_run += c
        ord_c = ord(c)
        # test if the character is a delete (backspace)
        if ord_c == 127:
            # backspace
            self.query = self.query[:-1]
        elif ord_c == 10:
            # enter
            self._run_key()
        elif c in ["1", "2", "3", "4", "5", "6"] and self.normal_mode:
            self.selected_row = int(c) - 1
            self._run_key()
        # elif ord_c == 27:
        # swap between modes via esc
        # self.normal_mode = not self.normal_mode
        elif ord_c == 9:
            # tab
            self.actions.edit_key(self.matched_keys[self.selected_row], block=True)
            self._setup_entries()
            self.reloaded = True
        elif c == "'":
            # tab
            self.actions.copy_entry_value_to_clipboard(
                self.matched_keys[self.selected_row]
            )
        elif ord_c == 47:
            # ?
            self.actions.search_in_google(self.query)
        # handle arrows
        elif ord_c == 66:
            if self.selected_row < len(self.matched_keys) - 1:
                self.selected_row = self.selected_row + 1
        elif ord_c == 65:
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
        elif c == ".":
            self.selected_query += 1
            self.query = self.get_previously_used_query(self.selected_query)
        elif c == ",":
            if self.selected_query >= 0:
                self.selected_query -= 1
            self.query = self.get_previously_used_query(self.selected_query)
        elif c == "+":
            sys.exit(0)
        elif ord_c == 68 or c == ";":
            # clean query shortcuts
            self.query = ""
        elif ord_c == 67:
            sys.exit(0)
        elif ord_c == 92 or c == ']':
            self._setup_entries()
            self.reloaded = True
        elif c == "-":
            # go up and clear
            self.selected_row = 0
            # remove the last word
            self.query = " ".join(
                list(filter(lambda x: x, self.query.split(" ")))[0:-1]
            )
            self.query += " "
        elif c.isalnum() or c == " ":
            self.query += c
            self.selected_row = 0

    def _run_key(self):
        self.actions.run_key(self.matched_keys[self.selected_row])
        statsd.increment("ps_run_key")
        self._get_data_warehouse().write_event(
            self.RUN_KEY_EVENT,
            {
                "query": self.query,
                "key": self.matched_keys[self.selected_row],
                "type_sequence": self.typed_up_to_run,
            },
        )

        statsd.gauge("ps_query_len_size", len(self.typed_up_to_run))
        self.typed_up_to_run = ""

    def get_previously_used_query(self, position) -> str:
        # len
        df = self._get_data_warehouse().event(self.RUN_KEY_EVENT)
        if position >= len(df):
            return ""

        return df.sort_values(by="tdw_timestamp", ascending=False).iloc[position]["key"]

    def _get_data_warehouse(self):
        if not self.tdw:
            from tiny_data_warehouse import DataWarehouse

            self.tdw = DataWarehouse()

        return self.tdw

    def print_highlighted(self, key: str, entry: Any) -> None:
        key_part = self.cf.bold(
            self.cf.selected(f" {self.control_size(key, self.MAX_KEY_SIZE)}")
        )
        body_part = f" {self.cf.bold(self.color_based_on_type(self.control_size(self.sanitize_content(entry.get_content_str(strip_new_lines=True)), self.MAX_CONTENT_SIZE), entry))} "
        print(key_part + body_part)

    def print_normal_row(self, key, entry):
        key_input = self.control_size(key, self.MAX_KEY_SIZE)
        body_part = self.color_based_on_type(
            self.control_size(
                self.sanitize_content(entry.get_content_str(strip_new_lines=True)),
                self.MAX_CONTENT_SIZE,
            ),
            entry,
        )
        print(f" {key_input} {body_part} ")

    def color_based_on_type(self, content, entry):
        type = entry.get_type_str()
        if type == "snippet":
            return self.cf.yellow(content)
        elif type == "cli_cmd" or type == "cmd":
            return self.cf.red(content)
        elif type == "url":
            return self.cf.green(content)
        elif type == "file":
            return self.cf.green(content)

        return content

    def sanitize_content(self, line) -> str:
        """
        Transform content into suitable to display in terminal row
        """
        line = line.strip()
        line = line.replace("\\r\\n", "")
        return line

    def control_size(self, a_string, num_chars):
        """
        Cuts when there is too long string and ads spaces when htere are too few.
        """
        if len(a_string) > num_chars:
            return a_string[0 : num_chars - 3] + "..."
        else:
            return a_string + " " * (num_chars - len(a_string))


def main():
    try:
        asyncio.run(SearchTerminalUi().run())
    except Exception as e:
        import traceback

        print(e)
        traceback.print_exc()
        breakpoint()


if __name__ == "__main__":
    main()
