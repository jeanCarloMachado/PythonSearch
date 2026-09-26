import json
from unittest.mock import patch

from python_search.search.entries_loader import EntriesLoader


def _print_entries(entries: dict, capsys, noise: str = ""):
    def load_entries():
        # Entries modules can print while they load; that must not reach stdout.
        if noise:
            print(noise)
        return entries

    with patch("python_search.search.entries_loader.ConfigurationLoader") as loader:
        loader.return_value.load_entries.side_effect = load_entries
        EntriesLoader.print_entries()
    return capsys.readouterr()


def test_print_entries_writes_records_as_json(capsys):
    captured = _print_entries(
        {
            "open mail": {"url": "https://mail.example.com", "shortcuts": ["⌥M"]},
            "launcher": {"cmd": "ps_ui show", "shortcut": "capslock"},
        },
        capsys,
    )

    records = {record["key"]: record for record in json.loads(captured.out)}
    assert records["open mail"]["type"] == "url"
    assert records["open mail"]["content"] == "https://mail.example.com"
    assert records["open mail"]["shortcuts"] == ["⌥M"]
    assert records["launcher"]["shortcut"] == "capslock"


def test_print_entries_keeps_loading_output_off_stdout(capsys):
    captured = _print_entries({"note": {"snippet": "hello"}}, capsys, noise="Loaded 1 keys")

    assert json.loads(captured.out) == [
        {"key": "note", "type": "snippet", "content": "hello"}
    ]
    assert "Loaded 1 keys" in captured.err
