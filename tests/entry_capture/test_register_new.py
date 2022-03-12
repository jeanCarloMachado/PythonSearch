from search_run.entry_capture.register_new import \
    transform_into_anonymous_entry


def test_only_value():
    input_data = "a snippet"

    result = transform_into_anonymous_entry(input_data)
    assert result[0].startswith("no key ")
    assert result[1] == {
        "snippet": "a snippet",
    }
