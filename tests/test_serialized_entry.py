from python_search.search.search_ui.serialized_entry import (
    decode_serialized_data_from_entry_text,
)


def test_decode_serialized_data_from_plain_entry_returns_empty_dict():
    assert decode_serialized_data_from_entry_text("machado taxes folder") == {}


def test_decode_serialized_data_from_empty_payload_returns_empty_dict():
    assert decode_serialized_data_from_entry_text("entry:") == {}
