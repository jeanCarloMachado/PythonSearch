import unittest

from search_run.interpreter.main import Interpreter
from search_run.interpreter.url import UrlInterpreter

from search_run.context import Context
from search_run.interpreter.cmd import CmdInterpreter
from search_run.interpreter.file import FileInterpreter
from search_run.interpreter.snippet import SnippetInterpreter
from tests.utils import build_config


class MatchingTestCase(unittest.TestCase):
    def test_cmd(self):
        config = build_config({"test jean": "pwd"})
        interpreter = Interpreter(config, Context()).get_interpreter("test jean")
        assert type(interpreter) is CmdInterpreter
        assert "pwd" == interpreter.cmd["cmd"]

    def test_url(self):
        a_url = "https://app.circleci.com/pipelines/github/jeanCarloMachado"
        config = build_config({"foo": a_url})
        interpreter = Interpreter(config, Context()).get_interpreter("foo")
        assert type(interpreter) is UrlInterpreter
        assert a_url == interpreter.cmd["url"]

    def test_snippet(self):
        content = "content"
        config = build_config({"foo": {"snippet": content}})
        interpreter = Interpreter(config, Context()).get_interpreter("foo")
        assert type(interpreter) is SnippetInterpreter
        assert content == interpreter.cmd["snippet"]

    def test_file(self):
        file = "/etc/passwd"
        config = build_config({"foo": file})
        interpreter = Interpreter(config, Context()).get_interpreter("foo")
        assert type(interpreter) is FileInterpreter
        assert file == interpreter.cmd["file"]
