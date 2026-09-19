use criterion::{criterion_group, criterion_main, Criterion};
use ps_core::{paths, Index, UsageStats};
use std::hint::black_box;

/// Benchmarks the real 10k-entry dump, since synthetic corpora hide the cost that matters:
/// the per-keystroke pass over every entry.
fn search_benchmark(c: &mut Criterion) {
    let mut index = match Index::load(&paths::entries_dump()) {
        Ok(index) => index,
        Err(error) => {
            eprintln!("skipping bench, no entries dump: {error}");
            return;
        }
    };
    index.set_usage(UsageStats::load());

    let mut group = c.benchmark_group("search");
    // Progressive prefixes of a realistic query: the first keystroke is the worst case because
    // almost everything matches.
    for query in ["c", "cl", "clv", "clv m", "clv mod", "clv model"] {
        group.bench_function(query, |b| {
            b.iter(|| black_box(index.search(black_box(query))))
        });
    }
    group.finish();
}

criterion_group!(benches, search_benchmark);
criterion_main!(benches);
