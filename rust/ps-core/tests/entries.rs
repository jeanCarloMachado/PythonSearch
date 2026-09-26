use ps_core::actions::parse_entries;
use ps_core::entry::EntryType;

#[test]
fn parses_the_records_printed_by_print_entries() {
    let json = r#"[
        {"key": "open mail", "type": "url", "content": "https://mail.example.com", "shortcuts": ["⌥M", "⌘⇧M"]},
        {"key": "launcher", "type": "cli_cmd", "content": "ps_ui show", "shortcut": "capslock"},
        {"key": "note", "type": "snippet", "content": "hello"}
    ]"#;

    let entries = parse_entries(json.as_bytes()).unwrap();

    assert_eq!(entries.len(), 3);
    assert_eq!(entries[0].key, "open mail");
    assert_eq!(entries[0].entry_type, EntryType::Url);
    assert_eq!(entries[1].entry_type, EntryType::CliCmd);
}

#[test]
fn shortcut_hint_comes_from_either_field() {
    let json = r#"[
        {"key": "a", "type": "url", "content": "x", "shortcuts": ["⌥M", "⌘⇧M"]},
        {"key": "b", "type": "cli_cmd", "content": "y", "shortcut": "capslock"},
        {"key": "c", "type": "snippet", "content": "z"}
    ]"#;

    let entries = parse_entries(json.as_bytes()).unwrap();

    assert_eq!(entries[0].shortcut(), Some("⌥M"));
    assert_eq!(entries[1].shortcut(), Some("capslock"));
    assert_eq!(entries[2].shortcut(), None);
}

#[test]
fn rejects_output_that_is_not_json() {
    assert!(parse_entries(b"Loaded 10 keys\n[]").is_err());
}
