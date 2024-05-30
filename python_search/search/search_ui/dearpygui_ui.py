

import dearpygui.dearpygui as dpg

from python_search.search.search_ui.bm25_search import Bm25Search

dpg.create_context()

import subprocess
import json

output = subprocess.getoutput("pys _entries_loader load_entries_as_json ")
commands = json.loads(output)

search_bm25 = Bm25Search(
    commands, number_entries_to_return=10
)

with dpg.value_registry():
    dpg.add_string_value(default_value="", tag="query")
    dpg.add_string_value(default_value="", tag="Entry1")
    dpg.add_string_value(default_value="", tag="Entry2")
    dpg.add_string_value(default_value="", tag="Entry3")
    dpg.add_string_value(default_value="", tag="Entry4")
    dpg.add_string_value(default_value="", tag="Entry5")
    dpg.add_string_value(default_value="", tag="Entry6")
    dpg.add_string_value(default_value="", tag="Entry7")
    dpg.add_string_value(default_value="", tag="Entry8")
    dpg.add_string_value(default_value="", tag="Entry9")
    dpg.add_string_value(default_value="", tag="Entry10")

with dpg.window(label="PythonSearch", no_title_bar=True, no_bring_to_front_on_focus=True):
    dpg.add_input_text(label="query", source="query", width=800, show=True, enabled=True)
    dpg.add_text(source="Entry1", label="Entry1")
    dpg.add_text(source="Entry2", label="Entry2")
    dpg.add_text(source="Entry3", label="Entry3")
    dpg.add_text(source="Entry4", label="Entry4")
    dpg.add_text(source="Entry5", label="Entry5")
    dpg.add_text(source="Entry6", label="Entry6")
    dpg.add_text(source="Entry7", label="Entry7")
    dpg.add_text(source="Entry8", label="Entry8")
    dpg.add_text(source="Entry9", label="Entry9")
    dpg.add_text(source="Entry10", label="Entry10")


dpg.create_viewport(title='Custom Title', width=800, height=300)
dpg.setup_dearpygui()
dpg.show_viewport()

# below replaces, start_dearpygui()
while dpg.is_dearpygui_running():
    # insert here any code you would like to run in the render loop
    # you can manually stop by using stop_dearpygui()
    query = dpg.get_value('query')
    result = search_bm25.search(query)

    for i in range(10):
        dpg.set_value(f'Entry{i+1}', result[i])

    dpg.render_dearpygui_frame()

dpg.destroy_context()