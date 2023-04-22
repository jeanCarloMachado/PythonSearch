import sys
import fire

from python_search.apps.clipboard import Clipboard


class CollectInput:
    """
    GUI window to capture user input and returns the entered data. It also allows the user to prefill the input field with content from their clipboard.
    """

    def launch(
        self,
        name="Enter Data",
        default_content="",
        prefill_with_clipboard: bool = False,
        set_as_clipboard: bool = False,
    ):
        """
        Launch the _entries capture GUI.
        """
        import contextlib

        with contextlib.redirect_stdout(None):
            import PySimpleGUI as sg

            if prefill_with_clipboard:
                default_content = Clipboard().get_content()

            font_size = 14
            sg.theme("SystemDefault1")

            input_field = sg.Input(
                key="content",
                default_text=default_content,
                expand_x=True,
                expand_y=True,
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
                alpha_channel=0.99,
            )

            if default_content != "":
                input_field.update(select=True)
            # workaround for mac bug
            window.read(timeout=100)
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
        result = values["content"]
        if set_as_clipboard:
            Clipboard().set_content(result)
        return result


def main():
    fire.Fire(CollectInput().launch)


if __name__ == "__main__":
    main()
