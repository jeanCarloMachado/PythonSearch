import logging
from subprocess import CalledProcessError
from typing import Optional

from grimoire.file import append_file
from grimoire.shell import shell as s
from grimoire.string import chomp, emptish


class AskQuestion:
    def ask(self, message: str) -> str:

        result = Rofi(title=message).open()

        if emptish(result):
            raise AskQuestionException.empty_content()

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


class Rofi:
    def __init__(
        self, title="Run: ", history_file=None, options_file=None, accept_empty=False
    ):
        self.title = title
        self.history_file = history_file
        self.accept_empty = accept_empty
        self.options_file = options_file

    def open(
        self, get_options_cmd: Optional[str] = None, accept_empty: Optional[bool] = None
    ) -> str:

        if accept_empty != None:
            self.accept_empty = accept_empty

        entries_cmd = ""
        if self.history_file:
            entries_cmd = f"tac {self.history_file} | "
        if self.options_file:
            entries_cmd = f"tac {self.options_file} | "

        # Tried things that did not work:
        cmd = f"""{entries_cmd} nice -19 rofi\
          -width 1000\
          -l 0 \
          -show-match\
          -dmenu\
          -p '{self.title}'"""

        if get_options_cmd:
            cmd = f"{get_options_cmd} | {cmd}"

        try:
            result = s.check_output(cmd)
        except CalledProcessError:
            result = ""
            return result

        logging.info(f"Rofi result: {result}")

        result = chomp(result)
        if emptish(result) and not self.accept_empty:
            raise MenuException.given_empty_value()

        if self.history_file:
            append_file(self.history_file, f"\n{result}\n")

        return result


class MenuException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def given_empty_value():
        return MenuException("No option selected in rofi!")
