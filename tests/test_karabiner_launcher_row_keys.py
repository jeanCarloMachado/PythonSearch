from python_search.shortcut.mac_karabiner_elements import MacKarabinerElements


def _parse(shortcut):
    return MacKarabinerElements(configuration=None).parse_mac_shortcut(shortcut, {}, "some key")["manipulators"][0]


def test_cmd_digit_yields_to_the_launcher_while_it_is_frontmost():
    manipulator = _parse("⌘1")
    assert manipulator["conditions"] == [{"type": "frontmost_application_unless", "file_paths": ["/ps_ui$"]}]


def test_other_shortcuts_stay_global():
    for shortcut in ["⌘⇧1", "⌥1", "⌘k", "⌃2"]:
        assert "conditions" not in _parse(shortcut), shortcut
