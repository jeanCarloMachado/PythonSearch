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

/// One record of the JSON printed by `python_search _entries_loader print_entries`.
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
    pub shortcuts: Vec<String>,
    #[serde(default)]
    pub shortcut: Option<String>,
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

    /// `created_at` as seconds since the unix epoch, or `None` when it is missing or unparseable.
    ///
    /// The Python side writes `YYYY-MM-DDTHH:MM:SS.ffffff` in local time without an offset. Only the
    /// date is read: creation recency is measured in weeks, so the hour and timezone do not matter.
    pub fn created_timestamp(&self) -> Option<f64> {
        let date = self.created_at.as_deref()?.get(..10)?;
        let mut parts = date.split('-').map(|p| p.parse::<i64>().ok());
        let (year, month, day) = (parts.next()??, parts.next()??, parts.next()??);
        if !(1..=12).contains(&month) || !(1..=31).contains(&day) {
            return None;
        }
        Some((days_from_civil(year, month, day) * 86_400) as f64)
    }

    /// The shortcut glyphs to show as a hint on the row, if the entry has one bound.
    pub fn shortcut(&self) -> Option<&str> {
        self.shortcuts
            .first()
            .map(String::as_str)
            .or(self.shortcut.as_deref())
    }
}

/// Days since 1970-01-01 for a proleptic Gregorian date (Howard Hinnant's `days_from_civil`).
fn days_from_civil(year: i64, month: i64, day: i64) -> i64 {
    let year = if month <= 2 { year - 1 } else { year };
    let era = year.div_euclid(400);
    let year_of_era = year - era * 400;
    let month_index = (month + 9) % 12;
    let day_of_year = (153 * month_index + 2) / 5 + day - 1;
    let day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    era * 146_097 + day_of_era - 719_468
}
