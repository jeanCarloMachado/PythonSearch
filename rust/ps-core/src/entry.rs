use serde::Deserialize;
use std::fmt;

/// The kind of an entry, inferred on the Python side by `Entry.get_type_str()`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntryType {
    Url,
    File,
    Snippet,
    CliCmd,
    Callable,
}

impl EntryType {
    /// Short label rendered in the type chip.
    pub fn label(self) -> &'static str {
        match self {
            EntryType::Url => "url",
            EntryType::File => "file",
            EntryType::Snippet => "snip",
            EntryType::CliCmd => "cmd",
            EntryType::Callable => "fn",
        }
    }
}

impl fmt::Display for EntryType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.label())
    }
}

/// One record of `~/.python_search/data/entries.json`.
#[derive(Debug, Clone, Deserialize)]
pub struct Entry {
    pub key: String,
    #[serde(rename = "type")]
    pub entry_type: EntryType,
    #[serde(default)]
    pub content: String,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub created_at: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub mac_shortcuts: Vec<String>,
    #[serde(default)]
    pub mac_shortcut: Option<String>,
}

impl Entry {
    /// What the UI shows on the right hand side of a row.
    ///
    /// Mirrors `SearchTerminalUi.sanitize_content`: URLs drop their scheme so the meaningful part of
    /// the host is visible in the limited width available.
    pub fn display_content(&self) -> &str {
        let content = self.content.trim();
        if self.entry_type == EntryType::Url {
            if let Some(rest) = content.strip_prefix("https://") {
                return rest;
            }
            if let Some(rest) = content.strip_prefix("http://") {
                return rest;
            }
        }
        content
    }

    /// The shortcut glyphs to show as a hint on the row, if the entry has one bound.
    pub fn shortcut(&self) -> Option<&str> {
        self.mac_shortcuts
            .first()
            .map(String::as_str)
            .or(self.mac_shortcut.as_deref())
    }
}
