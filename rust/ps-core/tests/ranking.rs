use ps_core::entry::{Entry, EntryType};
use ps_core::{Index, UsageStats};

fn entry(key: &str, entry_type: EntryType, content: &str) -> Entry {
    serde_json::from_value(serde_json::json!({
        "key": key,
        "type": match entry_type {
            EntryType::Url => "url",
            EntryType::File => "file",
            EntryType::Snippet => "snippet",
            EntryType::CliCmd => "cli_cmd",
            EntryType::Callable => "callable",
        },
        "content": content,
    }))
    .unwrap()
}

fn fixture() -> Index {
    Index::from_entries(vec![
        entry("git status update", EntryType::CliCmd, "git status"),
        entry("clv model deep dives", EntryType::Url, "https://example.com/clv"),
        entry("sdp q3 roadmap", EntryType::Url, "https://example.com/roadmap"),
        entry("unrelated thing", EntryType::Snippet, "git status update lives here"),
        entry("another unrelated", EntryType::Snippet, "nothing to see"),
    ])
}

fn top_key<'a>(index: &'a mut Index, query: &str) -> String {
    let matches = index.search(query);
    assert!(!matches.is_empty(), "no matches for {query:?}");
    index.entry(matches[0].index).key.clone()
}

#[test]
fn initials_find_the_entry() {
    let mut index = fixture();
    assert_eq!(top_key(&mut index, "gsu"), "git status update");
}

#[test]
fn a_key_match_outranks_a_content_match() {
    let mut index = fixture();
    // "unrelated thing" contains the phrase in its content, but the real entry owns it as a key.
    assert_eq!(top_key(&mut index, "git status update"), "git status update");
}

#[test]
fn content_is_searchable_when_the_key_does_not_match() {
    let mut index = fixture();
    let matches = index.search("nothing to see");
    let keys: Vec<&str> = matches
        .iter()
        .map(|m| index.entry(m.index).key.as_str())
        .collect();
    assert!(keys.contains(&"another unrelated"), "got {keys:?}");
}

#[test]
fn highlight_offsets_cover_the_typed_characters() {
    let mut index = fixture();
    let matches = index.search("clv");
    let first = &matches[0];
    assert!(first.matched_key);
    assert_eq!(first.key_indices, vec![0, 1, 2]);
}

#[test]
fn empty_query_returns_most_recently_used_first() {
    let mut index = fixture();

    // Without history the list still shows entries, in natural order, like the terminal UI did.
    assert_eq!(index.search("").len(), index.len());

    // Ordering follows *recency*, matching RecentKeys.get_latest_used_keys, so a more frequently
    // run entry does not outrank one that was used more recently.
    let mut usage = UsageStats::default();
    let now = ps_core::usage::now();
    usage.record("sdp q3 roadmap", now - 100.0);
    usage.record("sdp q3 roadmap", now - 90.0);
    usage.record("clv model deep dives", now - 10.0);
    index.set_usage(usage);

    assert_eq!(top_key(&mut index, ""), "clv model deep dives");
}

#[test]
fn usage_breaks_ties_without_overriding_relevance() {
    let mut index = fixture();
    let mut usage = UsageStats::default();
    // Heavily used, but a much worse textual match for "clv".
    for _ in 0..50 {
        usage.record("unrelated thing", ps_core::usage::now());
    }
    index.set_usage(usage);

    assert_eq!(top_key(&mut index, "clv"), "clv model deep dives");
}

#[test]
fn urls_drop_their_scheme_for_display() {
    let index = fixture();
    let url = index
        .entries()
        .iter()
        .find(|e| e.entry_type == EntryType::Url)
        .unwrap();
    assert_eq!(url.display_content(), "example.com/clv");
}
