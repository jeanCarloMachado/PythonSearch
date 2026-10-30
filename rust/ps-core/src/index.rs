use crate::bm25::{truncate_chars, Bm25};
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

/// How much a BM25 hit adds, as a fraction of the best fuzzy score for the query. The top BM25 entry
/// gets the full amount, the rest proportionally less. Half: enough that whole-word relevance
/// reorders fuzzy near-ties and surfaces words deep in the content, not enough to bury a clean key
/// match under an entry that merely mentions the words.
const BM25_WEIGHT: f32 = 0.5;

/// How much the usage boost can inflate a score, as a fraction. Applied multiplicatively so it
/// reorders near-ties without letting a frequently used entry outrank a clearly better match.
const USAGE_INFLUENCE: f32 = 0.35;

/// Half life of the creation recency boost, in seconds. A month: an entry added this week is
/// probably what the user is about to look for, one from last year has no claim to it.
const CREATED_HALF_LIFE: f64 = 30.0 * 24.0 * 3600.0;

/// How much creation recency adds to the boost, on the same scale as usage (roughly 0..=2.5). A new
/// entry has no run history yet, so without this it would start at the very bottom of every tie.
const WEIGHT_CREATED: f32 = 1.0;

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
    /// `created_at` per entry as a unix timestamp, parallel to `entries`. 0 when unknown.
    created: Vec<f64>,
    /// `usage.boost()` plus creation recency per entry, parallel to `entries`. Precomputed because the boost depends on
    /// wall clock time, and calling `SystemTime::now()` once per entry per keystroke dominated the
    /// search cost.
    boosts: Vec<f32>,
    matcher: Matcher,
    bm25: Bm25,
    /// Reused across queries so the hot loop never allocates.
    scratch: Vec<Match>,
    /// Which entries already have a fuzzy match this query, so later passes do not re-score them.
    fuzzy_matched: Vec<bool>,
    /// This query's BM25 score per entry, parallel to `entries`, zero for entries it did not match.
    bm25_scores: Vec<f32>,
    bm25_hits: Vec<u32>,
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
        let bm25 = Bm25::build(&entries);
        let created = entries
            .iter()
            .map(|e| e.created_timestamp().unwrap_or(0.0))
            .collect();

        let mut index = Index {
            entries,
            bm25,
            haystacks,
            usage: UsageStats::default(),
            created,
            boosts: vec![0.0; capacity],
            last_used: vec![0.0; capacity],
            matcher: Matcher::new(Config::DEFAULT),
            scratch: Vec::with_capacity(capacity),
            fuzzy_matched: vec![false; capacity],
            bm25_scores: vec![0.0; capacity],
            bm25_hits: Vec::new(),
            indices_buffer: Vec::with_capacity(64),
        };
        // Creation recency applies before usage history has loaded, and without any.
        index.refresh_boosts();
        index
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
        self.boosts.extend(
            self.entries
                .iter()
                .zip(&self.created)
                .map(|(e, &created)| self.usage.boost_at(&e.key, now) + created_boost(created, now)),
        );
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

        // BM25 first: it is an inverted index lookup, so it costs only as much as the query words'
        // postings, and its hits tell the content pass below which entries are worth scoring.
        let (scores, hits) = (&mut self.bm25_scores, &mut self.bm25_hits);
        let bm25_best = self.bm25.search(query, |index, score| {
            scores[index] = score;
            hits.push(index as u32);
        });

        // Phase one: keys only. This is the cheap pass and it satisfies most queries.
        self.fuzzy_matched.fill(false);
        for (index, haystack) in self.haystacks.iter().enumerate() {
            // `Pattern::indices` costs several times more than `score`, so highlight offsets are
            // computed afterwards for the handful of rows the UI will actually draw.
            let Some(score) = pattern.score(haystack.key.slice(..), &mut self.matcher) else {
                continue;
            };
            self.fuzzy_matched[index] = true;
            scratch.push(Match {
                index,
                score: score as f32,
                key_indices: Vec::new(),
                matched_key: true,
            });
        }

        // Phase two: content. A fuzzy content hit is weighted low enough that it could not displace
        // a key hit on its own, so when the key pass already filled the result list only the BM25
        // hits are scored, since BM25 may lift them. Skipping the rest is what keeps a multi word
        // query under a millisecond over 10k entries.
        let content_candidates: Box<dyn Iterator<Item = usize>> = if scratch.len() < MAX_RESULTS {
            Box::new(0..self.entries.len())
        } else {
            Box::new(self.bm25_hits.iter().map(|&index| index as usize))
        };
        for index in content_candidates {
            if self.fuzzy_matched[index] {
                continue;
            }
            let content = self.haystacks[index].content.slice(..);
            let Some(score) = pattern.score(content, &mut self.matcher) else {
                continue;
            };
            self.fuzzy_matched[index] = true;
            scratch.push(Match {
                index,
                score: score as f32 * CONTENT_WEIGHT,
                key_indices: Vec::new(),
                matched_key: false,
            });
        }

        // Entries only BM25 found: the words are there, but past the fuzzy content haystack, or
        // spelled in a way the fuzzy pattern does not accept as a whole.
        for &index in &self.bm25_hits {
            if !self.fuzzy_matched[index as usize] {
                scratch.push(Match {
                    index: index as usize,
                    score: 0.0,
                    key_indices: Vec::new(),
                    matched_key: false,
                });
            }
        }

        // Fuse. BM25 is scaled to the query's best fuzzy score so the two are in the same units
        // whatever the query length; with no fuzzy match at all, BM25 alone orders the results.
        let fuzzy_best = scratch.iter().map(|m| m.score).fold(0.0f32, f32::max);
        let bm25_scale = if fuzzy_best > 0.0 { fuzzy_best } else { 1.0 };
        for m in &mut scratch {
            let bm25 = if bm25_best > 0.0 {
                self.bm25_scores[m.index] / bm25_best
            } else {
                0.0
            };
            let relevance = m.score + BM25_WEIGHT * bm25_scale * bm25;
            m.score = relevance * (1.0 + USAGE_INFLUENCE * self.boosts[m.index]);
        }
        for &index in &self.bm25_hits {
            self.bm25_scores[index as usize] = 0.0;
        }
        self.bm25_hits.clear();

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

/// 1 for an entry created today, halving every [`CREATED_HALF_LIFE`], 0 when the date is unknown.
fn created_boost(created: f64, now: f64) -> f32 {
    if created <= 0.0 {
        return 0.0;
    }
    let age = (now - created).max(0.0);
    WEIGHT_CREATED * 0.5f64.powf(age / CREATED_HALF_LIFE) as f32
}
