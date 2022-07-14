import sys

import fire


def launch(name="Enter Data"):
    """
    Launch the data capture GUI.
    """
    import PySimpleGUI as sg

    font_size = 12
    sg.theme("SystemDefault1")

    layout = [
        [
            sg.Input(
                key="content",
            )
        ],
        [sg.Button("Continue", key="write")],
    ]

    window = sg.Window(name, layout, finalize=True, font=("Helvetica", font_size))
    window["content"].bind("<Return>", "_Enter")

    while True:
        event, values = window.read()
        if event == "write" or event == "content_Enter":
            break
        if event == sg.WINDOW_CLOSED:
            sys.exit(1)

    window.close()

    return values["content"]


if __name__ == "__main__":
    fire.Fire(launch)
