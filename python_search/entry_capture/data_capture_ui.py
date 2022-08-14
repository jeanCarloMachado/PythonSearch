import os
import time

from python_search.apps.terminal import Terminal


class AskQuestion:
    def ask(self, message: str) -> str:

        message = self._sanitize_message(message)
        content_file = "/tmp/python_search_input"
        if os.path.exists(content_file):
            os.remove(content_file)

        cmd = f"""kitty {Terminal.GENERIC_TERMINAL_PARAMS} bash -c 'printf "{message}: "; read tmp; echo "$tmp" >{content_file}' &"""
        os.system(cmd)

        while not os.path.exists(content_file):
            time.sleep(1)

        time.sleep(0.2)

        with open(content_file) as file:
            result = file.readlines()[0].strip()

        return result

    def _sanitize_message(self, message):
        allowed_chars = [" ", ":", "\n"]
        return "".join(
            char for char in message if char.isalnum() or char in allowed_chars
        )
