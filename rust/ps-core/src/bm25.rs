use crate::entry::Entry;
use std::collections::HashMap;

/// Term frequency saturation. The textbook value: a word repeated in a snippet stops adding much
/// after the first few occurrences.
const K1: f32 = 1.2;

/// Length normalisation. Long snippets would otherwise win on sheer word count.
const B: f32 = 0.75;

/// Field weights, folded into one weighted term frequency per entry (a simplified BM25F). The key
/// is what the user wrote to find the entry, so a word there counts more than one in the content.
const KEY_WEIGHT: f32 = 3.0;
const DESCRIPTION_WEIGHT: f32 = 2.0;
const TAG_WEIGHT: f32 = 2.0;
const CONTENT_WEIGHT: f32 = 1.0;

/// Content is truncated to this many characters before tokenising. Far deeper than the fuzzy
/// haystack, which is the point of BM25 here, but bounded so a pasted log does not bloat the index.
const MAX_CONTENT_CHARS: usize = 4096;

/// The last query word is matched as a prefix while it is being typed, so `clv mod` already finds
/// `model`. Prefixes shorter than this, or that expand to more terms than [`MAX_PREFIX_TERMS`],
/// are matched exactly instead: they say too little to be worth the postings walk.
const MIN_PREFIX_LEN: usize = 2;
const MAX_PREFIX_TERMS: usize = 64;

/// An inverted index over every entry's key, description, tags and content, scored with Okapi BM25.
///
/// Complements the fuzzy matcher rather than replacing it: nucleo is good at initials and typos in
/// keys, BM25 at whole words anywhere in the entry, weighted by how rare they are.
pub struct Bm25 {
    /// Sorted by term, so a prefix resolves to a contiguous range with two binary searches.
    terms: Vec<(String, u32)>,
    term_ids: HashMap<String, u32>,
    /// Per term: `(entry index, weighted term frequency)`.
    postings: Vec<Vec<(u32, f32)>>,
    idf: Vec<f32>,
    /// Per entry: the `K1 * (1 - B + B * len / avg_len)` part of the denominator, which only depends
    /// on the entry, precomputed so scoring a posting is a multiply and a divide.
    length_norm: Vec<f32>,
    /// Reused per query so scoring never allocates once warm.
    totals: Vec<f32>,
    term_best: Vec<f32>,
    touched: Vec<u32>,
    term_touched: Vec<u32>,
}

impl Bm25 {
    pub fn build(entries: &[Entry]) -> Self {
        let mut term_ids: HashMap<String, u32> = HashMap::new();
        let mut postings: Vec<Vec<(u32, f32)>> = Vec::new();
        let mut lengths = Vec::with_capacity(entries.len());
        let mut frequencies: HashMap<u32, f32> = HashMap::new();

        for (index, entry) in entries.iter().enumerate() {
            frequencies.clear();
            let mut length = 0.0;
            let mut add = |text: &str, weight: f32| {
                for token in tokenize(text) {
                    let next_id = term_ids.len() as u32;
                    let id = *term_ids.entry(token).or_insert(next_id);
                    *frequencies.entry(id).or_insert(0.0) += weight;
                    length += weight;
                }
            };
            add(&entry.key, KEY_WEIGHT);
            if let Some(description) = &entry.description {
                add(description, DESCRIPTION_WEIGHT);
            }
            for tag in &entry.tags {
                add(tag, TAG_WEIGHT);
            }
            add(truncate_chars(&entry.content, MAX_CONTENT_CHARS), CONTENT_WEIGHT);

            postings.resize_with(term_ids.len(), Vec::new);
            for (&id, &frequency) in &frequencies {
                postings[id as usize].push((index as u32, frequency));
            }
            lengths.push(length);
        }

        let count = entries.len() as f32;
        let idf = postings
            .iter()
            .map(|list| {
                let df = list.len() as f32;
                // The "+1" variant: never negative, so a word in most entries still helps a little.
                ((count - df + 0.5) / (df + 0.5) + 1.0).ln()
            })
            .collect();

        let avg_len = (lengths.iter().sum::<f32>() / count.max(1.0)).max(1.0);
        let length_norm = lengths
            .iter()
            .map(|length| K1 * (1.0 - B + B * length / avg_len))
            .collect();

        let mut terms: Vec<(String, u32)> =
            term_ids.iter().map(|(t, &id)| (t.clone(), id)).collect();
        terms.sort_unstable_by(|a, b| a.0.cmp(&b.0));

        Bm25 {
            terms,
            term_ids,
            postings,
            idf,
            length_norm,
            totals: vec![0.0; entries.len()],
            term_best: vec![0.0; entries.len()],
            touched: Vec::new(),
            term_touched: Vec::new(),
        }
    }

    /// Score every entry containing at least one query word. Calls `visit(entry, score)` once per
    /// such entry, in no particular order. Returns the highest score, or 0 when nothing matched.
    pub fn search(&mut self, query: &str, mut visit: impl FnMut(usize, f32)) -> f32 {
        let tokens: Vec<String> = tokenize(query).collect();
        // A trailing space means the last word is finished, so it no longer needs prefix expansion.
        let typing_last = !query.ends_with(char::is_whitespace);

        for (position, token) in tokens.iter().enumerate() {
            let as_prefix = typing_last
                && position + 1 == tokens.len()
                && token.chars().count() >= MIN_PREFIX_LEN;
            let ids = self.term_range(token, as_prefix);
            self.score_term(ids);
        }

        let mut best = 0.0f32;
        for &index in &self.touched {
            let score = self.totals[index as usize];
            best = best.max(score);
            visit(index as usize, score);
            self.totals[index as usize] = 0.0;
        }
        self.touched.clear();
        best
    }

    /// The term ids a query word stands for: itself, plus every indexed word it is a prefix of
    /// when `as_prefix` and the expansion is narrow enough to mean something.
    fn term_range(&self, token: &str, as_prefix: bool) -> Vec<u32> {
        if as_prefix {
            let start = self.terms.partition_point(|(t, _)| t.as_str() < token);
            let end = start
                + self.terms[start..]
                    .iter()
                    .take(MAX_PREFIX_TERMS + 1)
                    .take_while(|(t, _)| t.starts_with(token))
                    .count();
            if end - start <= MAX_PREFIX_TERMS {
                return self.terms[start..end].iter().map(|(_, id)| *id).collect();
            }
        }
        self.term_ids.get(token).map(|&id| vec![id]).unwrap_or_default()
    }

    /// Add one query word's contribution. When a prefix expands to several terms, an entry gets its
    /// best one rather than the sum, so `mod` does not reward an entry for holding both `model` and
    /// `modern`.
    fn score_term(&mut self, ids: Vec<u32>) {
        for id in ids {
            let idf = self.idf[id as usize];
            for &(index, frequency) in &self.postings[id as usize] {
                let norm = self.length_norm[index as usize];
                let score = idf * frequency * (K1 + 1.0) / (frequency + norm);
                let best = &mut self.term_best[index as usize];
                if *best == 0.0 {
                    self.term_touched.push(index);
                }
                *best = best.max(score);
            }
        }
        for &index in &self.term_touched {
            let total = &mut self.totals[index as usize];
            if *total == 0.0 {
                self.touched.push(index);
            }
            *total += self.term_best[index as usize];
            self.term_best[index as usize] = 0.0;
        }
        self.term_touched.clear();
    }
}

/// Lowercased runs of letters and digits. Punctuation, path separators and URL syntax all split, so
/// `https://example.com/clv` indexes `clv`.
fn tokenize(text: &str) -> impl Iterator<Item = String> + '_ {
    text.split(|c: char| !c.is_alphanumeric())
        .filter(|token| !token.is_empty())
        .map(str::to_lowercase)
}

pub(crate) fn truncate_chars(value: &str, max: usize) -> &str {
    match value.char_indices().nth(max) {
        Some((offset, _)) => &value[..offset],
        None => value,
    }
}
