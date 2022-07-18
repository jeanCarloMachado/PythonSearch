import fire


def launch(default_content=""):
    """
    Launch the data capture GUI.
    """
    import PySimpleGUI as sg

    sg.theme("SystemStandard1")
    font_size = 12

    layout = [
        [sg.Text("Enter Description:")],
        [sg.Input(key="key")],
        [sg.Text("Content:")],
        [sg.Input(key="content", default_text=default_content)],
        [sg.Button("Write", key="write")],
    ]

    window = sg.Window(
        "Capture entry", layout, font=("Helvetica", font_size), finalize=True
    )
    window["key"].bind("<Return>", "_Enter")

    while True:
        event, values = window.read()
        if event == "write" or event.endswith("_Enter"):
            break
        if event == sg.WINDOW_CLOSED:
            break

    window.close()

    return values["key"], values["content"], "type"


if __name__ == "__main__":
    fire.Fire(launch)
