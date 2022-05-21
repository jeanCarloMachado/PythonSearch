from search_run.interpreter.url import Url


def test_copy():
    url = "http://www.abc.com"
    entry = {"key_name": "abc", "url": url, "description": "more details"}

    assert url == Url(entry).copiable_part()
