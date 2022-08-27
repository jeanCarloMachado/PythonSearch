import sys

import fire

from python_search.apps.clipboard import Clipboard


class CollectInput:
    """
    Ask the user for input and return the entered data
    """

    def launch(self, name="Enter Data", prefill_with_clipboard: bool = False):
        """
        Launch the data capture GUI.
        """
        import PySimpleGUI as sg

        default_text = ""
        if prefill_with_clipboard:
            default_text = Clipboard().get_content()

        font_size = 12
        sg.theme("SystemDefault1")

        input_field = sg.Input(
            key="content", default_text=default_text, expand_x=True, expand_y=True
        )

        layout = [
            [input_field],
            [sg.Button("Continue", key="write")],
        ]

        window = sg.Window(
            name,
            layout,
            finalize=True,
            font=("Helvetica", font_size),
            alpha_channel=0.9,
        )

        # workaround for mac bug
        window.read(timeout=100)
        if default_text != "":
            input_field.update(select=True)
        window.set_alpha(1.0)

        window["content"].bind("<Return>", "_Enter")
        window["content"].bind("<Escape>", "_Esc")

        while True:
            event, values = window.read()

            if event and (event == "write" or event.endswith("_Enter")):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                sys.exit(1)

        window.close()

        return values["content"]


def main():
    fire.Fire(CollectInput().launch)


if __name__ == "__main__":
    main()
