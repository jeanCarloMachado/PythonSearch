import sys

import fire


class CollectInput:
    def launch(self, name="Enter Data"):
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

        window = sg.Window(
            name,
            layout,
            finalize=True,
            font=("Helvetica", font_size),
            alpha_channel=0.9,
        )

        # workaround for mac bug
        window.read(timeout=1000)
        window.set_alpha(1.0)

        window["content"].bind("<Return>", "_Enter")
        window["content"].bind("<Escape>", "_Esc")

        while True:
            event, values = window.read()
            if event == "write" or event.endswith("_Enter"):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                sys.exit(1)

        window.close()

        return values["content"]


def main():
    fire.Fire(CollectInput().launch)


if __name__ == "__main__":
    main()
