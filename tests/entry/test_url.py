import unittest

from search_run.interpreter.url import Url


class MyTestCase(unittest.TestCase):
    def test_create(self):
        """Test that initializing with str url does not throw exception"""
        Url("http://www.google.com")
        assert True

    def test_create_fails(self):
        """Test that initializing with str url does not throw exception"""
        self.assertRaises(Exception, Url, "not a url")
