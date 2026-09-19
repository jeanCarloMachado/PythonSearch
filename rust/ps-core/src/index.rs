use crate::entry::Entry;
use crate::usage::UsageStats;
use anyhow::{Context, Result};
use nucleo_matcher::pattern::{CaseMatching, Normalization, Pattern};
use nucleo_matcher::{Config, Matcher, Utf32String};
use std::path::Path;

/// How many results the UI is ever willing to show. Everything beyond this is discarded during
/// ranking rather than sorted.
pub const MAX_RESULTS: usize = 50;

/// A content hit is worth less than a key hit: the key is what the user wrote to find the entry.
const CONTENT_WEIGHT: f32 = 0.35;

/// Content is truncated to this many characters when building haystacks. Snippets can be
/// kilobytes long, and a match buried that deep is noise, not intent.
const MAX_CONTENT_HAYSTACK: usize = 96;

/// How much the usage boost can inflate a score, as a fraction. Applied multiplicatively so it
/// reorders near-ties without letting a frequently used entry outrank a clearly better match.
const USAGE_INFLUENCE: f32 = 0.35;

pub struct Match {
    pub index: usize,
    pub score: f32,
    /// Character offsets within the key that matched, for highlighting. Only populated for the
    /// results actually returned.
    pub key_indices: Vec<u32>,
    /// False when the entry matched on its content rather than its key.
    pub matched_key: bool,
}

/// Pre-tokenised haystacks for one entry. Building `Utf32String` once at load time keeps the
/// per-keystroke path allocation free.
struct Haystack {
    key: Utf32String,
    content: Utf32String,
}

pub struct Index {
    entries: Vec<Entry>,
    haystacks: Vec<Haystack>,
    usage: UsageStats,
    /// When each entry was last run, parallel to `entries`. Drives the empty-query ordering.
    last_used: Vec<f64>,
    /// `usage.boost()` per entry, parallel to `entries`. Precomputed because the boost depends on
    /// wall clock time, and calling `SystemTime::now()` once per entry per keystroke dominated the
    /// search cost.
    boosts: Vec<f32>,
    matcher: Matcher,
    /// Reused across queries so the hot loop never allocates.
    scratch: Vec<Match>,
    /// Which entries matched on their key in phase one, so phase two does not re-score them.
    key_matched: Vec<bool>,
    indices_buffer: Vec<u32>,
}

impl Index {
    pub fn load(path: &Path) -> Result<Self> {
        let contents = std::fs::read_to_string(path)
            .with_context(|| format!("could not read entries dump at {}", path.display()))?;
        let entries: Vec<Entry> = serde_json::from_str(&contents)
            .with_context(|| format!("malformed entries dump at {}", path.display()))?;
        Ok(Self::from_entries(entries))
    }

    pub fn from_entries(entries: Vec<Entry>) -> Self {
        let haystacks = entries
            .iter()
            .map(|entry| Haystack {
                key: Utf32String::from(entry.key.as_str()),
                content: Utf32String::from(truncate_chars(&entry.content, MAX_CONTENT_HAYSTACK)),
            })
            .collect();
        let capacity = entries.len();

        Index {
            entries,
            haystacks,
            usage: UsageStats::default(),
            boosts: vec![0.0; capacity],
            last_used: vec![0.0; capacity],
            matcher: Matcher::new(Config::DEFAULT),
            scratch: Vec::with_capacity(capacity),
            key_matched: vec![false; capacity],
            indices_buffer: Vec::with_capacity(64),
        }
    }

    pub fn set_usage(&mut self, usage: UsageStats) {
        self.usage = usage;
        self.refresh_boosts();
    }

    /// Record a run and refresh the affected boost immediately, so the next open already reflects it.
    pub fn record_run(&mut self, key: &str, timestamp: f64) {
        self.usage.record(key, timestamp);
        self.refresh_boosts();
    }

    /// Recompute every boost. Cheap relative to how rarely it happens (usage load, a run, or the
    /// periodic refresh that keeps recency decay honest across a long-lived daemon).
    pub fn refresh_boosts(&mut self) {
        let now = crate::usage::now();
        self.boosts.clear();
        self.boosts
            .extend(self.entries.iter().map(|e| self.usage.boost_at(&e.key, now)));
        self.last_used.clear();
        self.last_used
            .extend(self.entries.iter().map(|e| self.usage.last_used(&e.key)));
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn entry(&self, index: usize) -> &Entry {
        &self.entries[index]
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    /// Rank every entry against `query`. Runs entirely in memory; nothing here touches the
    /// filesystem or spawns a process.
    pub fn search(&mut self, query: &str) -> Vec<Match> {
        if query.trim().is_empty() {
            return self.most_used();
        }

        let pattern = Pattern::parse(query, CaseMatching::Ignore, Normalization::Smart);
        let mut scratch = std::mem::take(&mut self.scratch);
        scratch.clear();

        // Phase one: keys only. This is the cheap pass and it satisfies most queries.
        self.key_matched.fill(false);
        for (index, haystack) in self.haystacks.iter().enumerate() {
            // `Pattern::indices` costs several times more than `score`, so highlight offsets are
            // computed afterwards for the handful of rows the UI will actually draw.
            let Some(score) = pattern.score(haystack.key.slice(..), &mut self.matcher) else {
                continue;
            };
            self.key_matched[index] = true;
            scratch.push(Match {
                index,
                score: score as f32 * (1.0 + USAGE_INFLUENCE * self.boosts[index]),
                key_indices: Vec::new(),
                matched_key: true,
            });
        }

        // Phase two: content, only when the key pass did not already fill the result list. A
        // content hit is weighted low enough that it could not have displaced a key hit anyway, so
        // when there are enough key matches this whole pass is dead work. Skipping it is what keeps
        // a multi word query under a millisecond over 10k entries.
        if scratch.len() < MAX_RESULTS {
            for (index, haystack) in self.haystacks.iter().enumerate() {
                if self.key_matched[index] {
                    continue;
                }
                let Some(score) = pattern.score(haystack.content.slice(..), &mut self.matcher)
                else {
                    continue;
                };
                let score = score as f32 * CONTENT_WEIGHT;
                scratch.push(Match {
                    index,
                    score: score * (1.0 + USAGE_INFLUENCE * self.boosts[index]),
                    key_indices: Vec::new(),
                    matched_key: false,
                });
            }
        }

        // Partial sort: we only ever render the top MAX_RESULTS, so sorting the full match set is
        // wasted work when a common prefix matches thousands of entries.
        let keep = scratch.len().min(MAX_RESULTS);
        if scratch.len() > keep {
            scratch.select_nth_unstable_by(keep - 1, |a, b| Self::rank(&self.entries, a, b));
            scratch.truncate(keep);
        }
        scratch.sort_unstable_by(|a, b| Self::rank(&self.entries, a, b));

        let mut results: Vec<Match> = scratch.drain(..).collect();
        self.scratch = scratch;

        for result in &mut results {
            if !result.matched_key {
                continue;
            }
            self.indices_buffer.clear();
            pattern.indices(
                self.haystacks[result.index].key.slice(..),
                &mut self.matcher,
                &mut self.indices_buffer,
            );
            self.indices_buffer.sort_unstable();
            self.indices_buffer.dedup();
            result.key_indices = self.indices_buffer.clone();
        }

        results
    }

    /// Descending by score, with a stable tiebreak so equal scores do not shuffle between
    /// keystrokes. Key matches always outrank content-only matches at the same score.
    fn rank(entries: &[Entry], a: &Match, b: &Match) -> std::cmp::Ordering {
        b.score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| b.matched_key.cmp(&a.matched_key))
            .then_with(|| entries[a.index].key.len().cmp(&entries[b.index].key.len()))
            .then_with(|| entries[a.index].key.cmp(&entries[b.index].key))
    }

    /// The empty-query listing: most recently used first.
    ///
    /// This mirrors `RecentKeys.get_latest_used_keys` in
    /// `python_search/events/latest_used_entries.py` — unique keys ordered by when they were last
    /// run, most recent at the top — rather than inventing a different default order. It reads the
    /// whole history rather than that method's last 30 events, so the list stays full.
    ///
    /// Entries that have never been run follow, in their natural order, so the panel is never empty
    /// on a machine with no history.
    fn most_used(&self) -> Vec<Match> {
        let mut recent: Vec<usize> = (0..self.entries.len())
            .filter(|index| self.last_used[*index] > 0.0)
            .collect();

        recent.sort_unstable_by(|a, b| {
            self.last_used[*b]
                .partial_cmp(&self.last_used[*a])
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        recent.truncate(MAX_RESULTS);

        if recent.len() < MAX_RESULTS {
            let seen: std::collections::HashSet<usize> = recent.iter().copied().collect();
            for index in 0..self.entries.len() {
                if recent.len() >= MAX_RESULTS {
                    break;
                }
                if !seen.contains(&index) {
                    recent.push(index);
                }
            }
        }

        recent
            .into_iter()
            .map(|index| Match {
                index,
                score: self.boosts[index],
                key_indices: Vec::new(),
                matched_key: true,
            })
            .collect()
    }
}

fn truncate_chars(value: &str, max: usize) -> &str {
    match value.char_indices().nth(max) {
        Some((offset, _)) => &value[..offset],
        None => value,
    }
}
