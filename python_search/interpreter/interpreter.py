import logging
import re

from python_search.context import Context
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseEntry
from python_search.interpreter.cmd import CmdEntry
from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.group import GroupInterpreter
from python_search.interpreter.snippet import SnippetInterpreter
from python_search.interpreter.url import Url

INTERPETER_ORDER = [
    Url,
    FileInterpreter,
    GroupInterpreter,
    SnippetInterpreter,
    CmdEntry,
]


class Interpreter:
    """Matches a query with a entry"""

    _instance = None

    @staticmethod
    def build_instance(configuration):
        """
        Singleton. Initializes a configuration a context and a interpreter

        :return:
        """
        if not Interpreter._instance:
            context = Context.get_instance()
            Interpreter._instance = Interpreter(configuration, context)

        return Interpreter._instance

    def __init__(self, configuration, context: Context):
        self._configuration = configuration
        self.context = context
        self.context.set_interpreter(self)
        self.interpreters = INTERPETER_ORDER

    def default(self, given_input: str):
        """
        Applies the default behaviour to an interpreter
        """

        specific_interpreter = self.get_interpreter(given_input)

        return specific_interpreter.default()

    def clipboard(self, given_input: str):
        specific_interpreter: BaseEntry = self.get_interpreter(given_input)
        return specific_interpreter.interpret_clipboard()

    def get_interpreter(self, given_input: str) -> BaseEntry:
        """
        Given the content, returns the best matched interpreter.
        Returns the instance of the matched interpreter given an text input
        """
        self.context.set_input(given_input)
        key = self.get_key(given_input)

        try:
            given_input = self._configuration.get_command(key)
        except Exception as e:
            logging.error(e)

        return self._match_interpreter(given_input)

    def _match_interpreter(self, cmd):
        for interpreter in self.interpreters:
            try:
                logging.info(f"Trying to construct {interpreter}")
                command_instance = interpreter(cmd, self.context)
                logging.info(f"Matched command instance {command_instance}")
                return command_instance
            except CommandDoNotMatchException as e:
                pass

        raise Exception("Received a dict but did not match any type")

    def get_key(self, given_input) -> str:
        """
        @todo have a global way to match the keys and move the logic out of here
        this already caused a bug on key contents not being able to be copied
        """
        key_value = re.compile("([A-Za-z0-9 _-]+):(.*)")
        matches_kv = key_value.search(given_input)
        key = given_input
        if matches_kv:
            key = matches_kv.group(1)
        return key
