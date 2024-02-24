import unittest

from python_search.interpreter.url import UrlInterpreter


class TestUrlCase(unittest.TestCase):
    def test_create(self):
        """Test that initializing with str url does not throw exception"""
        UrlInterpreter("http://www.google.com")
        assert True

    def test_create_fails(self):
        """Test that initializing with str url does not throw exception"""
        self.assertRaises(Exception, UrlInterpreter, "not a url")
