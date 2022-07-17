import unittest

from python_search.context import Context
from python_search.interpreter.cmd import CmdEntry
from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.interpreter import Interpreter
from python_search.interpreter.snippet import SnippetInterpreter
from python_search.interpreter.url import Url
from tests.utils import build_config


class MatchingTestCase(unittest.TestCase):
    def test_cmd(self):
        config = build_config({"test jean": "pwd"})
        interpreter = Interpreter(config, Context()).get_interpreter("test jean")
        assert type(interpreter) is CmdEntry
        assert "pwd" == interpreter.cmd["cmd"]

    def test_url(self):
        a_url = "https://app.circleci.com/pipelines/github/jeanCarloMachado"
        config = build_config({"foo": {"url": a_url}})
        interpreter = Interpreter(config, Context()).get_interpreter("foo")
        assert type(interpreter) is Url
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
