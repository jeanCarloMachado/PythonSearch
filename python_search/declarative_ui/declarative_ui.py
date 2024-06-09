import sys


class DeclarativeUI:
    def __init__(self, title="The title"):
        self.title = title

    def build(self, spec: dict, title=None):
        """
        Launch the _entries capture GUI.
        Example DeclarativeUI().build([{"type": "text", "key": "key", "value": "value"}])
        """
        import PySimpleGUI as sg

        if title is not None:
            self.title = title

        font_size = 14
        sg.theme("SystemDefault1")

        layout = []

        first_key = None
        for item in spec:
            if "key" in item and first_key is None:
                first_key = item["key"]

            if item["type"] == "text":
                element = sg.Multiline(
                    default_text=item.get("value", ""),
                    key=item.get("key", ""),
                    expand_x=True,
                    expand_y=True,
                    font=("Helvetica", font_size),
                    size=item.get("size", (item.get("size", (20, 5)))),
                )
            elif item["type"] == "input":
                element = sg.Input(
                    item.get("value", ""),
                    key=item.get("key", ""),
                    expand_x=True,
                    expand_y=True,
                )
            elif item["type"] == "select":
                element = sg.Combo(
                    values=item.get("values", []),
                    default_value=item["value"],
                    key=item.get("key", ""),
                    expand_x=True,
                    expand_y=True,
                )

            layout.append([element])

        layout.append([sg.Button("Submit", key="write")])

        window = sg.Window(
            self.title,
            layout,
            finalize=True,
            font=("Helvetica", font_size),
            alpha_channel=0.99,
        )

        # workaround for mac bug
        window.read(timeout=100)
        window.set_alpha(1.0)

        if first_key:
            window[first_key].bind("<Return>", "_Enter")
            window[first_key].bind("<Escape>", "_Esc")

        while True:
            event, values = window.read()
            if event and (event == "write" or event.endswith("_Enter")):
                break
            if event == sg.WINDOW_CLOSED or event.endswith("_Esc"):
                sys.exit(1)

        window.close()
        return values
