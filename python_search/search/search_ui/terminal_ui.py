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
    DISPLAY_ROWS = 7  # Number of rows to display at once
    DEBOUNCE_DELAY_MS = 75  # 75ms debounce delay

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
        self._last_search_time = 0
        self.scroll_offset = 0  # For pagination
        self.all_matched_keys = []  # Store all search results

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
        self.scroll_offset = 0
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
        
        # Simple debouncing: only search if enough time has passed or query is different
        current_time = time.time() * 1000  # Convert to milliseconds
        should_search = (
            self.query != self.previous_query or 
            (current_time - self._last_search_time) >= self.DEBOUNCE_DELAY_MS
        )

        if should_search:
            self._last_search_time = current_time
            search_results = self.search_logic.search(self.query)
            self.all_matched_keys = list(search_results)
        # If not searching due to debounce, keep using previous results
        
        # Calculate visible range based on scroll offset
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.DISPLAY_ROWS, len(self.all_matched_keys))
        
        # Update matched_keys for backward compatibility
        self.matched_keys = self.all_matched_keys[start_idx:end_idx]
        
        current_display_row = 0
        for i in range(start_idx, end_idx):
            key = self.all_matched_keys[i]
            try:
                entry = Entry(key, self.commands[key])
            except Exception:
                entry = Entry(key, {"snippet": "Error loading entry"})

            # Adjust selected row to be relative to display
            if current_display_row == (self.selected_row - self.scroll_offset):
                self.print_highlighted(key, entry, i + 1)
            else:
                self.print_normal_row(key, entry, i + 1)

            current_display_row += 1
        
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
            self.selected_row = 0
            self.scroll_offset = 0
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
            if self.selected_row < len(self.all_matched_keys):
                self.actions.edit_key(self.all_matched_keys[self.selected_row], block=True)
                self._setup_entries()
                self.reloaded = True
        elif c == "'":
            # copy to clipboard
            if self.selected_row < len(self.all_matched_keys):
                self.actions.copy_entry_value_to_clipboard(
                    self.all_matched_keys[self.selected_row]
                )
        elif ord_c == 47:
            # ?
            self.actions.search_in_google(self.query)
        # handle arrows
        elif ord_c == 66:  # Down arrow
            if self.selected_row < len(self.all_matched_keys) - 1:
                self.selected_row = self.selected_row + 1
                # Check if we need to scroll down
                if self.selected_row >= self.scroll_offset + self.DISPLAY_ROWS:
                    self.scroll_offset = self.selected_row - self.DISPLAY_ROWS + 1
        elif ord_c == 65:  # Up arrow
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
                # Check if we need to scroll up
                if self.selected_row < self.scroll_offset:
                    self.scroll_offset = self.selected_row
        elif c == ".":
            self.selected_query += 1
            self.query = self.get_previously_used_query(self.selected_query)
            self.selected_row = 0
            self.scroll_offset = 0
        elif c == ",":
            if self.selected_query >= 0:
                self.selected_query -= 1
            self.query = self.get_previously_used_query(self.selected_query)
            self.selected_row = 0
            self.scroll_offset = 0
        elif c == "+":
            sys.exit(0)
        elif ord_c == 68 or c == ";":
            # clean query shortcuts
            self.query = ""
            self.selected_row = 0
            self.scroll_offset = 0
        elif ord_c == 67:
            sys.exit(0)
        elif ord_c == 92 or c == ']':
            self._setup_entries()
            self.reloaded = True
        elif c == "-":
            # go up and clear
            self.selected_row = 0
            self.scroll_offset = 0
            # remove the last word
            self.query = " ".join(
                list(filter(lambda x: x, self.query.split(" ")))[0:-1]
            )
            self.query += " "
        elif c.isalnum() or c == " ":
            self.query += c
            self.selected_row = 0
            self.scroll_offset = 0

    def _run_key(self):
        if self.selected_row < len(self.all_matched_keys):
            selected_key = self.all_matched_keys[self.selected_row]
            self.actions.run_key(selected_key)
            statsd.increment("ps_run_key")
            self._get_data_warehouse().write_event(
                self.RUN_KEY_EVENT,
                {
                    "query": self.query,
                    "key": selected_key,
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

    def print_highlighted(self, key: str, entry: Any, index: int) -> None:
        key_part = self.cf.bold(
            self.cf.selected(f"{index:2d}. {self.control_size(key, self.MAX_KEY_SIZE - 4)}")
        )
        body_part = f" {self.cf.bold(self.color_based_on_type(self.control_size(self.sanitize_content(entry.get_content_str(strip_new_lines=True)), self.MAX_CONTENT_SIZE), entry))} "
        print(key_part + body_part)

    def print_normal_row(self, key, entry, index):
        key_input = self.control_size(key, self.MAX_KEY_SIZE - 4)
        body_part = self.color_based_on_type(
            self.control_size(
                self.sanitize_content(entry.get_content_str(strip_new_lines=True)),
                self.MAX_CONTENT_SIZE,
            ),
            entry,
        )
        print(f"{index:2d}. {key_input} {body_part} ")

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
        SearchTerminalUi().run()
    except Exception as e:
        import traceback

        print(e)
        traceback.print_exc()
        breakpoint()


if __name__ == "__main__":
    main()
