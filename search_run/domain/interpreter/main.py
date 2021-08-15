import re

from loguru import logger as logging

from grimoire.event_sourcing.message import MessageBroker
from search_run.domain.context import Context
from search_run.domain.interpreter.base import (
    BaseInterpreter,
    CommandDoNotMatchException,
)
from search_run.domain.interpreter.cmd import CmdInterpreter
from search_run.domain.interpreter.file import FileInterpreter
from search_run.domain.interpreter.group import GroupInterpreter
from search_run.domain.interpreter.snippet import SnippetInterpreter
from search_run.domain.interpreter.url import UrlInterpreter
from grimoire.search_run.search_run_config import Configuration


class Interpreter:
    """Matches a query to a processor"""

    _instance = None

    @staticmethod
    def build_instance():
        if not Interpreter._instance:
            configuration = Configuration()
            context = Context.get_instance()
            Interpreter._instance = Interpreter(configuration, context)

        return Interpreter._instance

    def __init__(self, configuration, context: Context):
        self._configuration: Configuration = configuration
        self.context = context
        self.context.set_interpreter(self)
        self.message_passing = MessageBroker("run_key_command_performed")
        self.interpreters = [
            UrlInterpreter,
            FileInterpreter,
            GroupInterpreter,
            SnippetInterpreter,
            CmdInterpreter,
        ]

    def default(self, given_input: str):
        specific_interpreter = self.get_interpreter(given_input)
        return specific_interpreter.default()

    def clipboard(self, given_input: str):
        specific_interpreter: BaseInterpreter = self.get_interpreter(given_input)
        return specific_interpreter.interpret_clipboard()

    def get_interpreter(self, given_input: str) -> BaseInterpreter:
        self.context.set_input(given_input)
        """
        Returns the instance of the matched interpreter
        """
        key = self._get_key(given_input)
        self.message_passing.produce({"key": key})

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

    def _get_key(self, given_input):
        key_value = re.compile("([A-Za-z0-9 _-]+): (.*)")
        matches_kv = key_value.search(given_input)
        key = given_input
        if matches_kv:
            key = matches_kv.group(1)
        return key
