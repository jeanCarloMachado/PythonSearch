import datetime
from typing import Tuple


def test_only_value():
    input_data = "a snippet"

    result = transform_into_entry(input_data)
    assert result[0].startswith("no key ")
    assert result[1] == {
        "snippet": "a snippet",
    }


def transform_into_entry(given_input: str) -> Tuple[str, dict]:
    now = datetime.datetime.now()
    key = f"no key {now.strftime('%Y %M %d %H %M %S')}"
    return key, {
        "snippet": given_input,
    }
