import re

import logging

from search_run.context import Context
from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.cmd import CmdInterpreter
from search_run.interpreter.file import FileInterpreter
from search_run.interpreter.group import GroupInterpreter
from search_run.interpreter.snippet import SnippetInterpreter
from search_run.interpreter.url import UrlInterpreter


class Interpreter:
    """Matches a query to a processor"""

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
        self.interpreters = [
            UrlInterpreter,
            FileInterpreter,
            GroupInterpreter,
            SnippetInterpreter,
            CmdInterpreter,
        ]

    def default(self, given_input: str):
        """
        Applies the default behaviour to an interpreter
        """

        specific_interpreter = self.get_interpreter(given_input)

        return specific_interpreter.default()

    def clipboard(self, given_input: str):
        specific_interpreter: BaseInterpreter = self.get_interpreter(given_input)
        return specific_interpreter.interpret_clipboard()

    def get_interpreter(self, given_input: str) -> BaseInterpreter:
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

    def get_key(self, given_input):
        """
        @deprecated use it from searchresult instead
        :param given_input:
        :return:
        """
        key_value = re.compile("([A-Za-z0-9 _-]+): (.*)")
        matches_kv = key_value.search(given_input)
        key = given_input
        if matches_kv:
            key = matches_kv.group(1)
        return key

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
