import os
import sys
import select
from typing import Any
import json
import time
import shutil

from python_search.core_entities import Entry
from python_search.search.search_ui.QueryLogic import QueryLogic
from python_search.search.search_ui.search_actions import Actions
from python_search.search.search_ui.search_utils import setup_datadog

from python_search.apps.theme.theme import get_current_theme
from python_search.host_system.system_paths import SystemPaths
from python_search.logger import setup_term_ui_logger
from getch import getch

logger = setup_term_ui_logger()

startup_time = time.time_ns()
statsd = setup_datadog()

# disable hugging face warning about forking token paralelism when reloading entries
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class SearchTerminalUi:
    MAX_KEY_SIZE = 52  # Enlarged by 7 characters from previous 45
    MAX_CONTENT_SIZE = 53  # Reduced by 7 characters from previous 60
    RUN_KEY_EVENT = "python_search_run_key"
    DEFAULT_DISPLAY_ROWS = 7  # Default number of rows to display at once
    INPUT_DEBOUNCE_TIMEOUT = 0.005  # 5ms timeout - minimal delay to catch rapid input

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
        self.scroll_offset = 0  # For pagination
        self.all_matched_keys = []  # Store all search results
        self.query = ""
        self.selected_row = 0
        self.selected_query = -1
        self.display_rows = self._calculate_optimal_display_rows()

        # Query history cache - keep latest 50 queries in memory
        self.query_history_cache = []
        self.query_history_index = -1  # -1 means not browsing history
        self.MAX_QUERY_HISTORY = 50

        # Calculate dynamic sizes based on terminal width
        self._calculate_optimal_sizes()

        self._setup_entries()
        self._load_query_history_cache()

    def _calculate_optimal_display_rows(self) -> int:
        """Calculate optimal number of display rows based on terminal height"""
        try:
            # Get terminal size
            terminal_size = shutil.get_terminal_size()
            terminal_height = terminal_size.lines

            # Reserve space for:
            # - 1 line for the input/query line at the top
            # - 1 line for potential spacing/buffer
            # - Use remaining space for content rows
            reserved_lines = 2

            # Calculate optimal rows, ensuring we have at least 3 rows for content
            # Allow up to 9 rows for larger displays, but use DEFAULT_DISPLAY_ROWS as fallback
            max_rows = 9
            optimal_rows = max(3, min(max_rows, terminal_height - reserved_lines))

            # For very small terminals (height <= 10), reduce by 1 more to ensure typing line visibility
            if terminal_height <= 10:
                optimal_rows = max(3, optimal_rows - 1)

            logger.debug(f"Terminal height: {terminal_height}, " f"using optimized display rows: {optimal_rows}")
            return optimal_rows

        except Exception as e:
            logger.warning(f"Failed to calculate optimal display rows: {e}, using default")
            return self.DEFAULT_DISPLAY_ROWS

    def _calculate_optimal_sizes(self) -> None:
        """Calculate optimal key and content sizes based on terminal width"""
        try:
            terminal_size = shutil.get_terminal_size()
            terminal_width = terminal_size.columns

            # Reserve space for: "99. " (4 chars) + " " (1 char) = 5 chars
            available_width = terminal_width - 5

            # Allocate roughly 40% for keys, 60% for content
            key_width = max(30, min(50, int(available_width * 0.4)))
            content_width = available_width - key_width

            # Ensure content has a reasonable minimum
            if content_width < 40:
                key_width = available_width - 40
                content_width = 40

            # Adjust: enlarge key size by 7, reduce content by 7
            key_width += 7
            content_width -= 7

            # Ensure we don't go below reasonable minimums after adjustment
            if content_width < 33:  # Minimum content width after -7 adjustment
                adjustment = 33 - content_width
                key_width -= adjustment
                content_width = 33

            self.MAX_KEY_SIZE = key_width
            self.MAX_CONTENT_SIZE = content_width

            logger.debug(
                f"Terminal width: {terminal_width}, "
                f"Key size: {self.MAX_KEY_SIZE}, Content size: {self.MAX_CONTENT_SIZE}"
            )

        except Exception as e:
            logger.warning(f"Failed to calculate optimal sizes: {e}, using defaults")
            # Keep the class defaults if calculation fails

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
            # blocking function call - wait for first character
            c = self.get_caracter()
            logger.info("processing char" + c)
            query_changed = self.process_chars(c)

            if query_changed:
                # Show typed query immediately for instant feedback
                self._render_query_line()

                # Check if more input is coming (non-blocking) - if so, skip full render
                if self._has_pending_input():
                    continue

                # Query changed and no more pending input - do search and full render
                self.render(force_search=True)
            else:
                # Navigation only - render instantly without search
                self.render(force_search=False)

            self.previous_query = self.query

    @statsd.timed("ps_render")
    def render(self, force_search: bool = True):
        # Recalculate display rows and sizes in case terminal was resized
        new_display_rows = self._calculate_optimal_display_rows()
        if new_display_rows != self.display_rows:
            self.display_rows = new_display_rows
            # Adjust scroll offset if needed
            if self.selected_row >= self.scroll_offset + self.display_rows:
                self.scroll_offset = max(0, self.selected_row - self.display_rows + 1)

        # Recalculate optimal sizes for dynamic terminal width adjustment
        self._calculate_optimal_sizes()

        self.print_first_line()
        logger.info("rendering loop started")

        # Search only when needed - navigation uses cached results for instant response
        if force_search or not self.all_matched_keys:
            try:
                # search now returns a list, not a generator
                self.all_matched_keys = self.search_logic.search(self.query)
            except Exception as e:
                logger.error(f"Error during search: {e}")
                # Keep using previous results or empty list
                if self.all_matched_keys is None:
                    self.all_matched_keys = []

        # Calculate visible range based on scroll offset
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.display_rows, len(self.all_matched_keys))

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
            SystemPaths.get_binary_full_path("pys") + " _entries_loader load_entries_as_json 2>/dev/null"
        )
        # print("output", output)
        self.commands = json.loads(output)
        self.search_logic = QueryLogic(self.commands)

    def _load_query_history_cache(self):
        """Load the latest query history into memory cache"""
        try:
            df = self._get_data_warehouse().event(self.RUN_KEY_EVENT)
            if len(df) > 0:
                # Get unique queries sorted by most recent, limit to MAX_QUERY_HISTORY
                recent_queries = df.sort_values(by="tdw_timestamp", ascending=False)["query"].drop_duplicates()
                self.query_history_cache = recent_queries.head(self.MAX_QUERY_HISTORY).tolist()
            else:
                self.query_history_cache = []
        except Exception as e:
            logger.warning(f"Failed to load query history cache: {e}")
            self.query_history_cache = []

    def _add_query_to_history_cache(self, query: str):
        """Add a query to the history cache, maintaining max size and uniqueness"""
        if query and query.strip():
            # Remove query if it already exists
            if query in self.query_history_cache:
                self.query_history_cache.remove(query)

            # Add to front
            self.query_history_cache.insert(0, query)

            # Maintain max size
            if len(self.query_history_cache) > self.MAX_QUERY_HISTORY:
                self.query_history_cache = self.query_history_cache[: self.MAX_QUERY_HISTORY]

    def get_caracter(self) -> str:
        try:
            logger.info("getting char")
            c = getch()
            return c
        except Exception:
            return " "

    def _has_pending_input(self) -> bool:
        """
        Check if there's more input pending in stdin (non-blocking).
        Uses a short timeout to detect if user is still typing.

        Returns:
            True if more input is available, False if user has paused
        """
        readable, _, _ = select.select([sys.stdin], [], [], self.INPUT_DEBOUNCE_TIMEOUT)
        return bool(readable)

    def _render_query_line(self):
        """
        Render just the query line for instant typing feedback.
        This is called immediately after each keystroke so users see their input instantly.
        """
        content = self.cf.query(self.query)
        print("\x1b[2J\x1b[H" + self.cf.cursor(f"({len(self.commands)})> ") + f"{self.cf.bold(content)}")

    def print_first_line(self):
        content = self.cf.query(self.query)

        print("\x1b[2J\x1b[H" + self.cf.cursor(f"({len(self.commands)})> ") + f"{self.cf.bold(content)}")

    def process_chars(self, c: str) -> bool:
        """
        Process a single character input.
        Returns True if the query changed (needs search), False for navigation-only actions.
        """
        old_query = self.query
        self.typed_up_to_run += c
        ord_c = ord(c)
        # test if the character is a delete (backspace)
        if ord_c == 127:
            # backspace
            self.query = self.query[:-1]
            self.selected_row = 0
            self.scroll_offset = 0
            # Reset query history browsing when backspacing
            self.query_history_index = -1
        elif ord_c == 10:
            # enter
            self._run_key()
        elif c in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            # Run entry by number (1-9)
            entry_index = int(c) - 1
            if entry_index < len(self.all_matched_keys):
                self.selected_row = entry_index
                self._run_key()
        elif ord_c == 9:
            # tab
            if self.selected_row < len(self.all_matched_keys):
                self.actions.edit_key(self.all_matched_keys[self.selected_row], block=True)
                self._setup_entries()
                self.reloaded = True
        elif c == "'":
            # copy to clipboard
            if self.selected_row < len(self.all_matched_keys):
                self.actions.copy_entry_value_to_clipboard(self.all_matched_keys[self.selected_row])
        elif ord_c == 47:
            # ?
            self.actions.search_in_google(self.query)
        # handle arrows
        elif ord_c == 66:  # Down arrow
            if self.selected_row < len(self.all_matched_keys) - 1:
                self.selected_row = self.selected_row + 1
                # Check if we need to scroll down
                if self.selected_row >= self.scroll_offset + self.display_rows:
                    self.scroll_offset = self.selected_row - self.display_rows + 1
        elif ord_c == 65:  # Up arrow
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
                # Check if we need to scroll up
                if self.selected_row < self.scroll_offset:
                    self.scroll_offset = self.selected_row
                # Reset query history browsing when moving in results
                self.query_history_index = -1
            else:
                # Already at first item, loop through query history
                if self.query_history_cache:
                    if self.query_history_index == -1:
                        # Start browsing history from the beginning
                        self.query_history_index = 0
                    else:
                        # Move to next item in history
                        self.query_history_index = (self.query_history_index + 1) % len(self.query_history_cache)

                    # Set the query from history and refresh search
                    self.query = self.query_history_cache[self.query_history_index]
                    self.selected_row = 0
                    self.scroll_offset = 0
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
            # Reset query history browsing when clearing query
            self.query_history_index = -1
        elif ord_c == 67:
            sys.exit(0)
        elif ord_c == 92 or c == "]":
            self._setup_entries()
            self.reloaded = True
        elif c == "-":
            # go up and clear
            self.selected_row = 0
            self.scroll_offset = 0
            # remove the last word
            self.query = " ".join(list(filter(lambda x: x, self.query.split(" ")))[0:-1])
            self.query += " "
            # Reset query history browsing when modifying query
            self.query_history_index = -1
        elif c.isalnum() or c == " ":
            self.query += c
            self.selected_row = 0
            self.scroll_offset = 0
            # Reset query history browsing when typing
            self.query_history_index = -1

        # Return True if query changed (needs search), False for navigation
        return self.query != old_query

    def _run_key(self):
        if self.selected_row < len(self.all_matched_keys):
            selected_key = self.all_matched_keys[self.selected_row]
            self.actions.run_key(selected_key)
            statsd.increment("ps_run_key")

            # Add query to history cache before writing to data warehouse
            self._add_query_to_history_cache(self.query)

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
        key_part = self.cf.bold(self.cf.selected(f"{index: 2d}. {self.control_size(key, self.MAX_KEY_SIZE - 4)}"))
        content = self.sanitize_content(entry.get_content_str(strip_new_lines=True), entry)
        sized_content = self.control_size(content, self.MAX_CONTENT_SIZE)
        colored_content = self.color_based_on_type(sized_content, entry)
        body_part = f" {self.cf.bold(colored_content)} "
        print(key_part + body_part)

    def print_normal_row(self, key, entry, index):
        key_input = self.control_size(key, self.MAX_KEY_SIZE - 4)
        body_part = self.color_based_on_type(
            self.control_size(
                self.sanitize_content(entry.get_content_str(strip_new_lines=True), entry),
                self.MAX_CONTENT_SIZE,
            ),
            entry,
        )
        print(f"{index: 2d}. {key_input} {body_part} ")

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

    def sanitize_content(self, line, entry=None) -> str:
        """
        Transform content into suitable to display in terminal row
        """
        line = line.strip()
        line = line.replace("\\r\\n", "")

        # Remove http:// and https:// prefixes for URL entries
        if entry and entry.get_type_str() == "url":
            if line.startswith("https://"):
                line = line[8:]  # Remove "https://"
            elif line.startswith("http://"):
                line = line[7:]  # Remove "http://"

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
