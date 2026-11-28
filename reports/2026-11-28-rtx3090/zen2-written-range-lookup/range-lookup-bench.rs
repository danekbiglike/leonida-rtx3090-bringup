mod coverage { include!(env!("COVERAGE_SOURCE")); }
use coverage::Coverage;
use std::{hint::black_box, time::Instant};

fn main() {
    println!("ranges,queries,repetition,method,microseconds,covered");
    for count in [4usize, 8, 16, 32, 128, 512] {
        let mut state = 91u32;
        let mut rand = || {
            state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
            (state >> 12) as usize
        };
        let mut spans: Vec<_> = (0..count).map(|i| {
            let start = i * 23 + rand() % 13;
            (start, start + 1 + rand() % 34)
        }).collect();
        for i in (1..spans.len()).rev() { let j = rand() % (i + 1); spans.swap(i, j); }
        let queries: Vec<_> = (0..5500).map(|_| {
            let start = rand() % (count * 24);
            (start, start + 1 + rand() % 19)
        }).collect();
        let base = |&(first,last): &(usize, usize)| spans.iter().any(|&(a,b)| a <= first && last <= b);
        let idx = Coverage::from_ranges(spans.clone());
        assert!(queries.iter().all(|&(a,b)| base(&(a,b)) == idx.covers(a,b)));
        for repetition in 0..12 {
            for order in 0..2 {
                let indexed = (repetition + order) % 2 == 0;
                let start = Instant::now();
                let found = if indexed {
                    let view = Coverage::from_ranges(black_box(spans.clone()));
                    black_box(&queries).iter().filter(|&&(a,b)| view.covers(a,b)).count()
                } else {
                    black_box(&queries).iter().filter(|q| base(q)).count()
                };
                let us = start.elapsed().as_secs_f64() * 1e6;
                println!("{count},{},{repetition},{},{us:.3},{}", queries.len(),
                         if indexed { "indexed" } else { "linear" }, black_box(found));
            }
        }
    }
}
