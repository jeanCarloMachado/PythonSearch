""" Test that all main apis are not breaking """
import os

binary = "search_run"


def test_all():
    assert os.system("search_run --help") == 0
