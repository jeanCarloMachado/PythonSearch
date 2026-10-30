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

#[test]
fn bm25_finds_words_deep_in_the_content() {
    // Past the 96 characters the fuzzy content haystack sees.
    let long = format!("{} kubernetes rollout notes", "filler text ".repeat(20));
    let mut index = Index::from_entries(vec![
        entry("ops notes", EntryType::Snippet, &long),
        entry("another unrelated", EntryType::Snippet, "nothing to see"),
    ]);
    assert_eq!(top_key(&mut index, "kubernetes"), "ops notes");
}

#[test]
fn bm25_matches_the_last_word_as_a_prefix_while_typing() {
    let long = format!("{} kubernetes rollout notes", "filler text ".repeat(20));
    let mut index = Index::from_entries(vec![entry("ops notes", EntryType::Snippet, &long)]);
    assert_eq!(top_key(&mut index, "kubern"), "ops notes");
    // Once the word is finished with a space, it no longer expands.
    assert!(index.search("kubern ").is_empty());
}

#[test]
fn bm25_breaks_fuzzy_ties_by_word_relevance() {
    // Both keys fuzzy match "rust" identically, and the tiebreak alone would pick the shorter key.
    // Only "rust notes" is actually about rust beyond its title.
    let mut index = Index::from_entries(vec![
        entry("rust tips", EntryType::Url, "https://example.com/a"),
        entry("rust notes", EntryType::Snippet, "rust borrow checker and rust lifetimes"),
    ]);
    assert_eq!(top_key(&mut index, "rust"), "rust notes");
}

#[test]
fn recently_created_entries_win_ties() {
    let today = {
        let days = (ps_core::usage::now() / 86_400.0) as i64;
        // Civil date from days since epoch, to write today's created_at without a date crate.
        let z = days + 719_468;
        let era = z.div_euclid(146_097);
        let doe = z - era * 146_097;
        let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
        let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
        let mp = (5 * doy + 2) / 153;
        let day = doy - (153 * mp + 2) / 5 + 1;
        let month = if mp < 10 { mp + 3 } else { mp - 9 };
        let year = yoe + era * 400 + i64::from(month <= 2);
        format!("{year:04}-{month:02}-{day:02}T09:00:00.000000")
    };
    let with_date = |key: &str, created_at: &str| -> Entry {
        serde_json::from_value(serde_json::json!({
            "key": key, "type": "url", "content": "x", "created_at": created_at,
        }))
        .unwrap()
    };
    // Same fuzzy and BM25 score; the old one would win the alphabetical tiebreak.
    let mut index = Index::from_entries(vec![
        with_date("report a", "2021-03-01T00:00:00.000000"),
        with_date("report b", &today),
    ]);
    assert_eq!(top_key(&mut index, "report"), "report b");
}

#[test]
fn created_at_parses_to_a_unix_timestamp() {
    let entry: Entry = serde_json::from_value(serde_json::json!({
        "key": "k", "type": "url", "content": "x", "created_at": "2026-10-30T12:30:00.000000",
    }))
    .unwrap();
    assert_eq!(entry.created_timestamp(), Some(1_793_318_400.0));
}
