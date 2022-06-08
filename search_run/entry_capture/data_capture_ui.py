import os
import time


class AskQuestion:
    def ask(self, message: str) -> str:
        content_file = '/tmp/python_search_input'
        if os.path.exists(content_file):
            os.remove(content_file)

        cmd = f"""kitty bash -c 'printf "{message}: "; read tmp; echo "$tmp" >{content_file}' &"""
        os.system(cmd)

        while not os.path.exists(content_file):
            time.sleep(1)

        time.sleep(0.2)

        with open(content_file) as file:
            result = file.readlines()[0].strip()

        return result
