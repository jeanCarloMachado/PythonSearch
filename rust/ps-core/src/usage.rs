use serde::Deserialize;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Half life of the recency component, in seconds. Two weeks: an entry used daily stays hot,
/// one used once last quarter contributes almost nothing.
const RECENCY_HALF_LIFE: f64 = 14.0 * 24.0 * 3600.0;

/// How many past queries the launcher offers when arrowing up past the first row.
pub const MAX_QUERY_HISTORY: usize = 50;

const WEIGHT_FREQUENCY: f32 = 1.0;
const WEIGHT_RECENCY: f32 = 1.5;

#[derive(Deserialize)]
struct RunRecord {
    key: String,
    /// Unix timestamp, serialized as a string by the Python side.
    timestamp: Option<String>,
    /// What was typed to reach the entry. Empty for runs triggered by a shortcut.
    query_input: Option<String>,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct KeyUsage {
    pub count: u32,
    pub last_used: f64,
}

/// Aggregated history of which entries actually get run.
///
/// PythonSearch has been collecting this in `~/.python_search/data/searches_performed/` for years
/// (one JSON file per run) but never used it for ranking. It is the strongest available signal for
/// what the user means by a short query.
#[derive(Debug, Default)]
pub struct UsageStats {
    by_key: HashMap<String, KeyUsage>,
    max_count: u32,
    /// Distinct queries (or keys, for runs logged without one) that led to a run, most recent
    /// first, capped at [`MAX_QUERY_HISTORY`].
    recent_queries: Vec<String>,
}

impl UsageStats {
    /// Read every run event from disk. ~19 MB across ~4.8k files, so this runs on a background
    /// thread at daemon start rather than blocking the first frame.
    pub fn load() -> Self {
        let mut stats = UsageStats::default();
        let mut queries: Vec<(f64, String)> = Vec::new();
        let dir = crate::paths::searches_performed_dir();
        let Ok(read_dir) = std::fs::read_dir(&dir) else {
            return stats;
        };

        for dir_entry in read_dir.flatten() {
            let path = dir_entry.path();
            if path.extension().and_then(|e| e.to_str()) != Some("json") {
                continue;
            }
            let Ok(contents) = std::fs::read_to_string(&path) else {
                continue;
            };
            let Ok(record) = serde_json::from_str::<RunRecord>(&contents) else {
                continue;
            };
            let timestamp = record
                .timestamp
                .as_deref()
                .and_then(|t| t.parse::<f64>().ok())
                .unwrap_or(0.0);
            stats.record(&record.key, timestamp);
            // Runs logged before the query was recorded — and every run triggered by a shortcut —
            // have no query. The key itself is what the user would have to retype, so it stands in.
            let recall = record
                .query_input
                .filter(|q| !q.trim().is_empty())
                .unwrap_or_else(|| record.key.clone());
            queries.push((timestamp, recall));
        }

        // Newest first, keeping only the first occurrence of each query.
        queries.sort_by(|a, b| b.0.total_cmp(&a.0));
        let mut seen = std::collections::HashSet::new();
        stats.recent_queries = queries
            .into_iter()
            .map(|(_, query)| query)
            .filter(|query| seen.insert(query.clone()))
            .take(MAX_QUERY_HISTORY)
            .collect();

        stats
    }

    /// The queries that led to a run, most recent first.
    pub fn take_recent_queries(&mut self) -> Vec<String> {
        std::mem::take(&mut self.recent_queries)
    }

    pub fn record(&mut self, key: &str, timestamp: f64) {
        let usage = self.by_key.entry(key.to_string()).or_default();
        usage.count += 1;
        usage.last_used = usage.last_used.max(timestamp);
        self.max_count = self.max_count.max(usage.count);
    }

    pub fn get(&self, key: &str) -> Option<KeyUsage> {
        self.by_key.get(key).copied()
    }

    /// When this entry was last run, or 0 if never.
    pub fn last_used(&self, key: &str) -> f64 {
        self.by_key.get(key).map_or(0.0, |usage| usage.last_used)
    }

    pub fn is_empty(&self) -> bool {
        self.by_key.is_empty()
    }

    /// A score in roughly 0..=2.5, combining how often and how recently an entry was run.
    pub fn boost(&self, key: &str) -> f32 {
        self.boost_at(key, now())
    }

    /// Same as [`UsageStats::boost`] with the current time supplied by the caller, so a whole-corpus
    /// pass does not repeat the clock read for every entry.
    pub fn boost_at(&self, key: &str, now: f64) -> f32 {
        let Some(usage) = self.by_key.get(key) else {
            return 0.0;
        };

        // Normalised against the most used entry so the scale does not drift as history grows.
        let frequency = (usage.count as f32).ln_1p() / (self.max_count as f32).ln_1p().max(1.0);

        let age = (now - usage.last_used).max(0.0);
        let recency = 0.5f64.powf(age / RECENCY_HALF_LIFE) as f32;

        WEIGHT_FREQUENCY * frequency + WEIGHT_RECENCY * recency
    }
}

/// Seconds since the unix epoch.
pub fn now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}
