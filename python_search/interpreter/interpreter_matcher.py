import re

from python_search.context import Context
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter
from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.group import GroupInterpreter
from python_search.interpreter.python import PythonInterpreter
from python_search.interpreter.snippet import SnippetInterpreter
from python_search.interpreter.url import UrlInterpreter
from python_search.logger import interpreter_logger

INTERPRETERS_IN_ORDER = [
    UrlInterpreter,
    FileInterpreter,
    GroupInterpreter,
    SnippetInterpreter,
    PythonInterpreter,
    CmdInterpreter,
]


class InterpreterMatcher:
    """
    Matches a query with an entry interpreter
    """

    _instance = None

    @staticmethod
    def build_instance(configuration) -> "InterpreterMatcher":
        """
        Singleton. Initializes a _configuration a context and a interpreter

        :return:
        """
        if not InterpreterMatcher._instance:
            context = Context.get_instance()
            InterpreterMatcher._instance = InterpreterMatcher(configuration, context)

        return InterpreterMatcher._instance

    def __init__(self, configuration, context: Context):
        self._configuration = configuration
        self.context = context
        self.context.set_interpreter(self)
        self._interpreters = INTERPRETERS_IN_ORDER
        self.logger = interpreter_logger()

    def get_interpreter(
        self, input_str: str
    ) -> BaseInterpreter:
        """
        Given the string content, returns the best matched interpreter.
        Returns the instance of the matched interpreter given an text input
        """
        self.context.set_input(input_str)

        try:
            # tries to get the real key if it exists
            key = self._get_key(input_str)
            input_str = self._configuration.get_command(key)
        except Exception as e:
            self.logger.error(e)

        return self._match_interpreter(input_str)

    def get_interpreter_from_type(self, type: str) -> BaseInterpreter:
        """
        From a type given in the ui via string returns the matching interpreter type

        """

        if type == "Snippet":
            return SnippetInterpreter

        if type == "Url":
            return UrlInterpreter

        if type == "Cmd":
            return CmdInterpreter

        if type == "File":
            return FileInterpreter

        raise Exception(f"Could not find a matching interpreter for string {type}")

    def default(self, input_str: str):
        """
        Applies the default behaviour to an interpreter
        """

        specific_interpreter = self.get_interpreter(input_str)

        return specific_interpreter.default()

    def clipboard(self, given_input: str):
        specific_interpreter: BaseInterpreter = self.get_interpreter(given_input)
        return specific_interpreter.interpret_clipboard()

    def _match_interpreter(self, cmd) -> BaseInterpreter:
        self.logger.info("Matching interpreter for command: %s", cmd)
        print("Matching interpreter for command: %s", cmd)
        for interpreter in self._interpreters:
            try:
                print(f"Trying to construct {interpreter}")
                command_instance = interpreter(cmd, self.context)
                print(f"Matched command instance {command_instance}")
                return command_instance
            except CommandDoNotMatchException as e:
                pass

        raise Exception("Received a dict but did not match any type")

    def _get_key(self, given_input) -> str:
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
