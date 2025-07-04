import sys
import fire

from python_search.apps.clipboard import Clipboard
from python_search.declarative_ui.declarative_ui import DeclarativeUI


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

        if prefill_with_clipboard:
            default_content = Clipboard().get_content()

        with contextlib.redirect_stdout(None):
            result = DeclarativeUI().build(
                [
                    {"key": "content", "type": "input", "value": default_content},
                ],
                title=name,
            )

        if set_as_clipboard:
            Clipboard().set_content(result["content"])
        return result["content"]


def main():
    fire.Fire(CollectInput().launch)


if __name__ == "__main__":
    main()
