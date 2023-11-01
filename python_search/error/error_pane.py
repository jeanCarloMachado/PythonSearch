import PySimpleGUI as sg

from python_search.environment import is_mac


def run(text=None):
    if not text:
        import sys

        data = sys.stdin.readlines()
        text = "\n".join(data)

    layout = [[sg.Text(text)], [sg.Button("Close")]]

    sg.theme("SystemDefault1")
    _FONT = "Menlo"
    # Create the window
    window = sg.Window(
        "Error Window",
        layout,
        font=(_FONT, 15),
    )

    # Create an event loop
    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event == "Close" or event == sg.WIN_CLOSED:
            break

    window.close()


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
