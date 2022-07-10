import fire
import json


def launch(default_content=""):
    import PySimpleGUI as sg

    pysearch_modes = [
        'URL', 'Command', 'Snippet', 'File'
    ]

    sg.theme("Dark Grey 12")
    width = max(map(len, pysearch_modes))+1

    layout = [
        [sg.Text("Enter Description:")],
        [sg.Input(key='key')],
        [sg.Text("Content:")],
        [sg.Input(key='content', default_text=default_content)],
        [sg.Text("Select Type:")],
        [sg.Combo(pysearch_modes, size=(width, 5), enable_events=True, key='type')],
        [sg.Button('Write', key='write')],
    ]

    window = sg.Window("Enter Values", layout, finalize=True)

    while True:
        event, values = window.read()
        if event == "write":
            break
        if event == sg.WINDOW_CLOSED:
            break

    window.close()

    return values["key"], values["content"], values["type"]


if __name__ == '__main__':
    fire.Fire(launch)
