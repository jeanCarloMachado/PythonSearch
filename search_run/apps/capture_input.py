import sys

import fire


def launch(name="Enter Data:"):
    """
    Launch the data capture GUI.
    """
    import PySimpleGUI as sg

    sg.theme("SystemDefault1")

    layout = [
        [sg.Text(name)],
        [sg.Input(key="content")],
        [sg.Button("Continue", key="write")],
    ]

    window = sg.Window("Capture input", layout, finalize=True)

    while True:
        event, values = window.read()
        if event == "write":
            break
        if event == sg.WINDOW_CLOSED:
            sys.exit(1)

    window.close()

    return values["content"]


if __name__ == "__main__":
    fire.Fire(launch)
