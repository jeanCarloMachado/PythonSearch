from python_search.entry_capture.entry_inserter_gui.entry_inserter_gui import (
    NewEntryGUI,
)
from python_search.apps.clipboard import Clipboard
from python_search.entry_capture.register_new import RegisterNew


class PromptEditor:
    """
    The purpose of this code is to launch a pre-defined prompt for the user to interact with CHATGPT and to furhter refine it
    """

    def launch_prompt(
        self,
        prompt_text: str = "",
        no_clipboard: bool = False,
    ):
        clipboard_content = Clipboard().get_content()

        if not no_clipboard:
            if prompt_text.find("<CLIPBOARD>"):
                key = prompt_text.replace("<CLIPBOARD>", clipboard_content)
            else:
                key = prompt_text + "\n" + clipboard_content
        else:
            key = prompt_text

        result = NewEntryGUI().launch(
            default_key=key,
            default_content="",
            generate_body=True,
        )
        RegisterNew().save_entry_data(result)

        return result


def main():
    import fire

    fire.Fire(PromptEditor().launch_prompt)
