"""
Declarative UI module for building simple form-based GUIs.

This module provides a declarative approach to creating PySimpleGUI forms,
allowing users to specify UI elements via a dictionary-based specification.
"""

import sys
from typing import TypedDict


class UIFieldSpec(TypedDict, total=False):
    """
    Specification for a single UI field element.

    Attributes:
        type: The widget type - "text" (multiline), "input" (single line), or "select" (dropdown).
        key: Unique identifier for the field, used to retrieve values after submission.
        value: Default value to populate the field with.
        values: List of options for "select" type fields.
        size: Tuple of (width, height) for sizing the widget.
    """

    type: str
    key: str
    value: str
    values: list[str]
    size: tuple[int, int]


class DeclarativeUI:
    """
    A declarative form builder that creates PySimpleGUI windows from specifications.

    This class simplifies the creation of input forms by accepting a list of field
    specifications and handling the window lifecycle, event binding, and value collection.

    Example:
        >>> ui = DeclarativeUI(title="My Form")
        >>> result = ui.build([
        ...     {"type": "input", "key": "name", "value": ""},
        ...     {"type": "select", "key": "color", "value": "red", "values": ["red", "blue"]}
        ... ])
    """

    def __init__(self, title: str = "The title") -> None:
        """
        Initialize the DeclarativeUI with a window title.

        Args:
            title: The title to display in the window title bar.
        """
        self.title = title

    def build(self, spec: list[UIFieldSpec], title: str | None = None) -> dict[str, str]:
        """
        Build and display a form window based on the provided specification.

        Creates a GUI window with form fields according to the spec, waits for user
        input, and returns the collected values. The window closes on Submit button,
        Enter key, or Escape key (exits with code 1).

        Args:
            spec: List of field specifications defining the form layout.
                  Each item should have a "type" key with value "text", "input", or "select".
            title: Optional title override for this specific build call.

        Returns:
            Dictionary mapping field keys to their entered values.

        Note:
            - The first field with a key gets Enter/Escape key bindings
            - Escape key or window close triggers sys.exit(1)
            - Enter key or Submit button returns the values
        """
        import PySimpleGUI as sg

        if title is not None:
            self.title = title

        font_size = 14
        sg.theme("SystemDefault1")

        layout: list[list[sg.Element]] = []
        first_key: str | None = None
        element: sg.Element

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
                    size=item.get("size", (20, 5)),
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

        # Workaround for macOS bug where window alpha doesn't apply correctly on first render
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
