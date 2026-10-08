def test_first():
    from python_search.entry_capture.register_new import RegisterNew

    # a first test to make sure it is importable
    assert RegisterNew is not None


def test_sanitize_key_removes_backslash():
    from python_search.entry_capture.register_new import RegisterNew

    assert RegisterNew._sanitize_key(None, "value add databricks\\") == "value add databricks"
