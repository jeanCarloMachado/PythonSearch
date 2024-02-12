import os
import sys
from typing import List, Any
from subprocess import PIPE, Popen

from getch import getch
import nltk
tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
lemmatizer = nltk.stem.WordNetLemmatizer()

from python_search.theme import get_current_theme
from python_search.core_entities.core_entities import Entry
theme = get_current_theme()
cf = theme.get_colorful()

MAX_LINE_SIZE=80
MAX_TITLE_SIZE=40
MAX_CONTENT_SIZE=47
NUMBER_ENTTRIES_RENDER=15

class TermUI:
    _documents = None

    def run(self):
        from python_search.configuration.loader import ConfigurationLoader;
        config = ConfigurationLoader().load_config()
        self.commands = config.commands
        entries: List[str] = list(self.commands.keys())

        os.system('clear')
        self.query = ''
        self.selected_row = 0
        # hide cursor
        print('\033[?25l', end="") 

        while True: 
            if self.query:
                tokenized_query = tokenize(self.query)
                self.matches = self.get_bm25().get_top_n(tokenized_query, entries, n=NUMBER_ENTTRIES_RENDER)
            else:
                self.matches = entries[0:NUMBER_ENTTRIES_RENDER]
                tokenized_query = []

            os.system('clear')
            print(cf.cursor(f"({len(self.commands)})> ")+ f"{cf.bold(cf.query(self.query))}" )

            self.print_entries(self.commands, tokenized_query)
            # build bm25 index while the user types
            self.get_bm25()
            c = getch() 
            self.process_chars(self.query, c)

    
    def print_entries(self, commands, tokenized_query):
        # print the matches
        for i, key in enumerate(self.matches):
            entry = Entry(key, commands[key])

            if i == self.selected_row:
                print_highlighted(key, entry)
            else:
                print_normal_row(key, entry, tokenized_query)

    def process_chars(self, query, c):
        ord_c = ord(c)
        # test if the character is a delete (backspace)
        if ord_c == 127:
            #backspace
            self.query = query[:-1]
        elif ord_c == 10:
            #enter
            command = f'run_key "{self.matches[self.selected_row]}" &>/dev/null'
            Popen(command, stdout=None, stderr=None, shell=True)
        elif ord_c == 9:
            #tab
            Popen(f'entries_editor edit_key "{self.matches[self.selected_row]}"  &>/dev/null', stdout=None, stderr=None, shell=True)
        elif ord_c == 92:
            #tab
            Popen(f'share_entry share_only_value "{self.matches[self.selected_row]}" &>/dev/null', stdout=None, stderr=None, shell=True)
        elif ord_c == 47:
            #?
            Popen(f'clipboard set_content "{query}"  && run_key "search in google using clipboard content" &>/dev/null', stdout=None, stderr=None, shell=True)
        elif ord_c == 66:
            self.selected_row = self.selected_row + 1
        elif ord_c == 65:
            self.selected_row = self.selected_row - 1
        elif c == '+':
            sys.exit(0)
        elif c == ';' or ord_c == 68:
            # clean query shortucts
            self.query=""
        elif ord_c == 39 or ord_c == 67:
            sys.exit(0)
        elif c == "-"  :
            # go up and clear
            self.selected_row = 0
            # remove the last word
            self.query = " ".join(list(filter(lambda x: x, self.query.split(" ")))[0:-1])
        elif c.isalnum() or c == " ":
            self.query += c
            self.selected_row = 0

    def get_bm25(self):
        if self._documents is None:
            self._documents = self.setup_documents()
        return self._documents

    def setup_documents(self):
        tokenized_corpus = [tokenize((key + str(value))) for key, value in self.commands.items()]
        from rank_bm25 import BM25Okapi as BM25
        bm25 = BM25(tokenized_corpus)

        return bm25


def tokenize(string):
    tokens = tokenizer.tokenize(string)
    lemmas = [lemmatizer.lemmatize(t) for t in tokens]
    return lemmas
        
def control_size(a_string, num_chars):
    """
    Cuts when there is too long string and ads spaces when htere are too few.
    """
    if len(a_string) > num_chars:
        return a_string[0:num_chars-3] + "..." 
    else:
        return a_string + " " * (num_chars - len(a_string))

def print_highlighted(key: str, entry: Any) -> None:
    key_part = cf.bold(cf.selected(f" {control_size(key, MAX_TITLE_SIZE)}"))
    body_part = f" {cf.bold(cf.entrycontentselected(control_size(entry.get_content_str(strip_new_lines=True).strip(),MAX_CONTENT_SIZE)))} "
    type_part = cf.entrytype(f"({entry.get_type_str()}) ")
    print( key_part + body_part + type_part)



def print_normal_row(key, entry, tokenized_query):
    key_input = control_size(key, MAX_TITLE_SIZE)
    key_part = " ".join([str(cf.partialmatch(key_fragment)) if key_fragment in tokenized_query else key_fragment for key_fragment in key_input.split(" ") ])
    body_part = cf.entrycontentunselected(control_size(entry.get_content_str(strip_new_lines=True).strip(),MAX_CONTENT_SIZE))
    print(f" {key_part} {body_part} " + cf.entrytype(f"({entry.get_type_str()})"))

def main():
    TermUI().run()

if __name__ == "__main__":
    main()