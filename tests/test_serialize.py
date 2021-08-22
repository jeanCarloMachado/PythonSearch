import unittest

import pytest

from search_run.interpreter.main import Interpreter

from search_run.context import Context
from tests.utils import build_config


@pytest.mark.skipif(
    True,
    reason="not ready yet",
)
class SerializeTestCase(unittest.TestCase):
    def test_cmd(self):

        config = build_config({"test jean": "pwd"})
        interpreter = Interpreter(config, Context())._get_interpeter("test jean")
        result = interpreter.serialize_entry()
        assert result == '"pwd": {"cmd": "pwd"}'
