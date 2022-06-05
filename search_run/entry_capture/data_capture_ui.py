import logging
from subprocess import CalledProcessError
from typing import Optional

from grimoire.file import append_file
from grimoire.shell import shell as s
from grimoire.string import chomp, emptish

import os
import time

class AskQuestion:
    def ask(self, message: str) -> str:
        content_file = '/tmp/python_search_input'
        if os.path.exists(content_file):
            os.remove(content_file)

        cmd = f"""kitty bash -c 'print {message}; read tmp; echo "$tmp" >{content_file}' &"""
        os.system(cmd)

        while not os.path.exists(content_file):
            time.sleep(1)

        time.sleep(0.2)

        with open(content_file) as file:
            result = file.readlines()[0].strip()

        return result

class AskQuestionException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def empty_content():
        return AskQuestionException(
            f"The value you gave to dmenu looks empty. Will not proceed"
        )


class MenuException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def given_empty_value():
        return MenuException("No option selected in rofi!")
