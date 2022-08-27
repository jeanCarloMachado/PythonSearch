from python_search.interpreter.urlinterpreter import UrlInterpreter


def test_copy():
    url = "http://www.abc.com"
    entry = {"key_name": "abc", "url": url, "description": "more details"}

    assert url == UrlInterpreter(entry).copiable_part()
