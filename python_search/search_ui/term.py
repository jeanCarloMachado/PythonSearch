import os
import sys
from typing import List, Any
from subprocess import PIPE, Popen

from getch import getch
import nltk

tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
lemmatizer = nltk.stem.WordNetLemmatizer()

from python_search.theme import get_current_theme
from python_search.core_entities.core_entities import Entry

theme = get_current_theme()
cf = theme.get_colorful()


class TermUI:
    MAX_LINE_SIZE = 80
    MAX_TITLE_SIZE = 40
    MAX_CONTENT_SIZE = 47
    NUMBER_ENTTRIES_RENDER = 15

    _documents = None

    def run(self):
        from python_search.configuration.loader import ConfigurationLoader

        config = ConfigurationLoader().load_config()
        self.commands = config.commands
        entries: List[str] = list(self.commands.keys())

        os.system("clear")
        self.query = ""
        self.selected_row = 0
        # hide cursor
        print("\033[?25l", end="")

        while True:
            if self.query:
                tokenized_query = self.tokenize(self.query)
                self.matches = self.get_bm25().get_top_n(
                    tokenized_query, entries, n=self.NUMBER_ENTTRIES_RENDER
                )
            else:
                self.matches = entries[0 : self.NUMBER_ENTTRIES_RENDER]
                tokenized_query = []

            os.system("clear")
            print(
                cf.cursor(f"({len(self.commands)})> ")
                + f"{cf.bold(cf.query(self.query))}"
            )

            self.print_entries(tokenized_query)
            # build bm25 index while the user types
            self.get_bm25()
            c = self.get_caracter()
            self.process_chars(self.query, c)

    def get_caracter(self):
        try:
            return getch()
        except Exception as e:
            print(e)
            return ""

    def print_entries(self, tokenized_query):
        # print the matches
        for i, key in enumerate(self.matches):
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
            command = f'run_key "{self.matches[self.selected_row]}" &>/dev/null'
            Popen(command, stdout=None, stderr=None, shell=True)
        elif ord_c == 9:
            # tab
            Popen(
                f'entries_editor edit_key "{self.matches[self.selected_row]}"  &>/dev/null',
                stdout=None,
                stderr=None,
                shell=True,
            )
        elif ord_c == 92:
            # tab
            Popen(
                f'share_entry share_only_value "{self.matches[self.selected_row]}" &>/dev/null',
                stdout=None,
                stderr=None,
                shell=True,
            )
        elif ord_c == 47:
            # ?
            Popen(
                f'clipboard set_content "{query}"  && run_key "search in google using clipboard content" &>/dev/null',
                stdout=None,
                stderr=None,
                shell=True,
            )
        elif ord_c == 66:
            self.selected_row = self.selected_row + 1
        elif ord_c == 65:
            self.selected_row = self.selected_row - 1
        elif c == "+":
            sys.exit(0)
        elif ord_c == 68 or c == "'":
            # clean query shortucts
            self.query = ""
        elif ord_c == 67 or c == ";":
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

    def get_bm25(self):
        if self._documents is None:
            self._documents = self.setup_documents()
        return self._documents

    def setup_documents(self):
        tokenized_corpus = [
            self.tokenize((key + str(value))) for key, value in self.commands.items()
        ]
        from rank_bm25 import BM25Okapi as BM25

        bm25 = BM25(tokenized_corpus)

        return bm25

    def print_highlighted(self, key: str, entry: Any) -> None:
        key_part = cf.bold(
            cf.selected(f" {self.control_size(key, self.MAX_TITLE_SIZE)}")
        )
        body_part = f" {cf.bold(cf.entrycontentselected(self.control_size(entry.get_content_str(strip_new_lines=True).strip(), self.MAX_CONTENT_SIZE)))} "
        type_part = cf.entrytype(f"({entry.get_type_str()}) ")
        print(key_part + body_part + type_part)

    def print_normal_row(self, key, entry, tokenized_query):
        key_input = self.control_size(key, self.MAX_TITLE_SIZE)
        key_part = " ".join(
            [
                str(cf.partialmatch(key_fragment))
                if key_fragment in tokenized_query
                else key_fragment
                for key_fragment in key_input.split(" ")
            ]
        )
        body_part = cf.entrycontentunselected(
            self.control_size(
                entry.get_content_str(strip_new_lines=True).strip(),
                self.MAX_CONTENT_SIZE,
            )
        )
        print(f" {key_part} {body_part} " + cf.entrytype(f"({entry.get_type_str()})"))

    def tokenize(self, string):
        tokens = tokenizer.tokenize(string)
        lemmas = [lemmatizer.lemmatize(t) for t in tokens]
        return lemmas

    def control_size(self, a_string, num_chars):
        """
        Cuts when there is too long string and ads spaces when htere are too few.
        """
        if len(a_string) > num_chars:
            return a_string[0 : num_chars - 3] + "..."
        else:
            return a_string + " " * (num_chars - len(a_string))


def main():
    TermUI().run()


if __name__ == "__main__":
    main()
