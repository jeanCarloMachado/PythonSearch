from python_search.search.search_ui.SearchLogic import SearchLogic


def test_first():
    entries = {
        "key 1": "value 1",
        "key 2": "value 2",
        "key 3": "value 3",
        "key 4": "value 4",
        "key 5": "value 5",
        "key 6": "value 6",
    }
    search = SearchLogic(entries)
    assert list(search.search("key 2"))[0] == "key 2"
    assert len(list(search.search(""))) == SearchLogic.NUMBER_ENTRIES_TO_RETURN