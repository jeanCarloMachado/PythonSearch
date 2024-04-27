import asyncio
import sys
from typing import Any

from getch import getch

from python_search.search_ui.bm25_search import Bm25Search
from python_search.search_ui.search_actions import Actions

from python_search.theme import get_current_theme
from python_search.core_entities.core_entities import Entry

class TermUI:
    MAX_LINE_SIZE = 80
    MAX_KEY_SIZE = 45
    MAX_CONTENT_SIZE = 40
    NUMBER_ENTRIES_TO_RETURN = 15


    _documents_future = None
    commands = None
    documents = None

    def __init__(self) -> None:
        self.theme = get_current_theme()
        self.cf = self.theme.get_colorful()
        self.actions = Actions()
        from python_search.configuration.loader import ConfigurationLoader
        self.commands = ConfigurationLoader().load_config().commands
        from python_search.configuration.loader import ConfigurationLoader
        self.commands = ConfigurationLoader().load_config().commands
        self.search = Bm25Search(number_entries_to_return=self.NUMBER_ENTRIES_TO_RETURN)


    async def run(self):
        """
        Rrun the application main loop
        """

        self.query = ""
        self.selected_row = 0
        # hide cursor
        self.print_first_line()
        self.hide_cursor()

        self.matches, selected_query_terms = self.search.search(query='')
        self.print_entries(self.matches, selected_query_terms)

        while True:
            self.print_first_line()
            self.matches, selected_query_terms = self.search.search(query=self.query)

            self.print_entries(self.matches, selected_query_terms)
            # build bm25 index while the user types

            c = self.get_caracter()
            self.process_chars(self.query, c)

    def hide_cursor(self):
        print("\033[?25l", end="")
    def get_caracter(self):
        try:
            return getch()
        except Exception as e:
            return " "

    def print_first_line(self):
        print(
            "\x1b[2J\x1b[H" +
            self.cf.cursor(f"({len(self.commands)})> ")
            + f"{self.cf.bold(self.cf.query(self.query))}"
        )

    def print_entries(self, matches, tokenized_query):
        # print the matches
        for i, key in enumerate(matches):
            entry = Entry(key, self.commands[key])

            if i == self.selected_row:
                self.print_highlighted(key, entry)
            else:
                self.print_normal_row(key, entry, tokenized_query)

    def process_chars(self, query, c):
        ord_c = ord(c)
        # test if the character is a delete (backspace)
        if ord_c == 127:
            # backspace
            self.query = query[:-1]
        elif ord_c == 10:
            # enter
            self.actions.run_key(self.matches[self.selected_row])
        elif ord_c == 9:
            # tab
            self.actions.edit_key(self.matches[self.selected_row])
        elif c == "'":
            # tab
            self.actions.copy_entry_value_to_clipboard(self.matches[self.selected_row])
        elif ord_c == 47:
            # ?
            self.actions.search_in_google(self.query)
        elif ord_c == 66 or c == '.':
            self.selected_row = self.selected_row + 1
        elif ord_c == 65 or c == ',':
            self.selected_row = self.selected_row - 1
        elif c == "+":
            sys.exit(0)
        elif ord_c == 68 or c == ';':
            # clean query shortcuts
            self.query = ""
        elif ord_c == 67 or c == "\\" :
            sys.exit(0)
        elif c == "-":
            # go up and clear
            self.selected_row = 0
            # remove the last word
            self.query = " ".join(
                list(filter(lambda x: x, self.query.split(" ")))[0:-1]
            )
            # append a space in the end to make easy to contruct the next work
            self.query += " "
        elif c.isalnum() or c == " ":
            self.query += c
            self.selected_row = 0

    def print_highlighted(self, key: str, entry: Any) -> None:
        key_part = self.cf.bold(
            self.cf.selected(f" {self.control_size(key, self.MAX_KEY_SIZE)}")
        )
        body_part = f" {self.cf.bold(self.cf.entrycontentselected(self.control_size(entry.get_content_str(strip_new_lines=True).strip(), self.MAX_CONTENT_SIZE)))} "
        type_part = self.cf.entrytype(f"{entry.get_type_str()} ")
        print(key_part + body_part + type_part)

    def print_normal_row(self, key, entry, tokenized_query):
        key_input = self.control_size(key, self.MAX_KEY_SIZE)
        key_part = " ".join(
            [
                str(self.cf.partialmatch(key_fragment))
                if key_fragment in tokenized_query
                else key_fragment
                for key_fragment in key_input.split(" ")
            ]
        )
        body_part = self.cf.entrycontentunselected(
            self.control_size(
                entry.get_content_str(strip_new_lines=True).strip(),
                self.MAX_CONTENT_SIZE,
            )
        )
        print(f" {key_part} {body_part} " + self.cf.entrytype(f"{entry.get_type_str()}"))

    def control_size(self, a_string, num_chars):
        """
        Cuts when there is too long string and ads spaces when htere are too few.
        """
        if len(a_string) > num_chars:
            return a_string[0 : num_chars - 3] + "..."
        else:
            return a_string + " " * (num_chars - len(a_string))




async def main_async():
    await TermUI().run()
def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
