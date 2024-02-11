import os
import sys
from typing import List
from subprocess import PIPE, Popen

from python_search.theme import get_current_theme
from python_search.core_entities.core_entities import Entry
theme = get_current_theme()
cf = theme.get_colorful()

MAX_LINE_SIZE=80
MAX_TITLE_SIZE=40
MAX_CONTENT_SIZE=47
NUMBER_ENTTRIES_RENDER=15

def main():
    from python_search.configuration.loader import ConfigurationLoader;
    config = ConfigurationLoader().load_config()
    commands = config.commands
    entries: List[str] = list(commands.keys())
    values = list(commands.values())

    tokenized_corpus = [(key + str(value)).split(" ") for key, value in commands.items()]
    from rank_bm25 import BM25Okapi as BM25
    bm25 = BM25(tokenized_corpus)

    from getch import getch

    os.system('clear')
    query = ''
    selected_row = 0
    redraw = True


    # hide cursor
    print('\033[?25l', end="") 

    while True: 
        enter_pressed = False


        if not query:
            matches = entries[0:NUMBER_ENTTRIES_RENDER]
            tokenized_query = []
        else:
            tokenized_query = query.split(" ")
            matches = bm25.get_top_n(tokenized_query, entries, n=NUMBER_ENTTRIES_RENDER)


        if redraw:
            os.system('clear')
            print(cf.cursor(f"({len(commands)})> ")+ f"{cf.bold(cf.query(query))}" )


        # print the matches
        if redraw:
            for i, key in enumerate(matches):
                entry = Entry(key, commands[key])

                if i == selected_row:
                    print_highlighted(key, entry)
                else:
                    print_normal_row(key, entry, tokenized_query)

        c = getch() 
        redraw = True
        ord_c = ord(c)
        # test if the character is a delete (backspace)
        if ord_c == 127:
            #backspace
            query = query[:-1]
            continue
        elif ord_c == 10:
            #enter
            command = f'run_key "{matches[selected_row]}" &>/dev/null'
            Popen(command, stdout=None, stderr=None, shell=True)
            continue
        elif ord_c == 9:
            #tab
            Popen(f'entries_editor edit_key "{matches[selected_row]}"  &>/dev/null', stdout=None, stderr=None, shell=True)
            continue
        elif ord_c == 92:
            #tab
            Popen(f'share_entry share_only_value "{matches[selected_row]}" &>/dev/null', stdout=None, stderr=None, shell=True)
            continue
        elif ord_c == 47:
            #?
            Popen(f'clipboard set_content "{query}"  && run_key "search in google using clipboard content" &>/dev/null', stdout=None, stderr=None, shell=True)
            continue
        elif ord_c == 66:
            selected_row = selected_row + 1
            continue
        elif ord_c == 65:
            selected_row = selected_row - 1
            continue
        elif c == '+':
            sys.exit(0)
            continue
        elif ord_c == 68 or c == ';':
            # clean query shortucts
            query=""
            continue
        elif ord_c == 39 or ord_c == 67:
            sys.exit(0)
            continue
        elif c == "-":
            # go up and clear
            selected_row = 0
            query = ''
        elif c.isalnum() or c == " ":
            query += c
            selected_row = 0

        
def control_size(a_string, num_chars):
    """
    Cuts when there is too long string and ads spaces when htere are too few.
    """
    if len(a_string) > num_chars:
        return a_string[0:num_chars-3] + "..." 
    else:
        return a_string + " " * (num_chars - len(a_string))

def print_highlighted(key, entry):
    key_part = cf.bold(cf.selected(f" {control_size(key, MAX_TITLE_SIZE)}"))
    body_part = f" {cf.bold(cf.entrycontentselected(control_size(entry.get_content_str(strip_new_lines=True).strip(),MAX_CONTENT_SIZE)))} "
    type_part = cf.entrytype(f"({entry.get_type_str()}) ")
    print( key_part + body_part + type_part)



def print_normal_row(key, entry, tokenized_query):
    key_input = control_size(key, MAX_TITLE_SIZE)
    key_part = " ".join([str(cf.partialmatch(key_fragment)) if key_fragment in tokenized_query else key_fragment for key_fragment in key_input.split(" ") ])
    body_part = cf.entrycontentunselected(control_size(entry.get_content_str(strip_new_lines=True).strip(),MAX_CONTENT_SIZE))
    print(f" {key_part} {body_part} " + cf.entrytype(f"({entry.get_type_str()})"))


if __name__ == "__main__":
    main()