mod clean_blocks;
use clean_blocks::CleanBlocks;
use std::collections::BTreeSet;
use std::hint::black_box;
use std::ops::Range;
use std::time::Instant;

fn old(blocks: &BTreeSet<usize>, scan: Range<usize>) -> u64 {
    let clean: Vec<_> = blocks.range(scan.clone()).copied().collect();
    if clean.len() == scan.len() {
        return 0;
    }
    let mut index = 0;
    let mut sum = 0;
    for block in scan {
        while index < clean.len() && clean[index] < block { index += 1; }
        if clean.get(index) != Some(&block) { sum += block as u64 + 1; }
    }
    sum
}

fn new(blocks: &CleanBlocks, scan: Range<usize>) -> u64 {
    blocks.missing(scan).into_iter().flatten().map(|b| b as u64 + 1).sum()
}

fn timed(mut f: impl FnMut() -> u64) -> u128 {
    let start = Instant::now();
    for _ in 0..1000 { black_box(f()); }
    start.elapsed().as_nanos() / 1000
}

fn main() {
    println!("blocks,dirty_stride,old_median_ns,new_median_ns");
    for size in [32, 512, 2784] {
        for stride in [0, 97, 8, 2] {
            let mut tree = BTreeSet::new();
            let mut runs = CleanBlocks::new();
            tree.extend(0..size);
            runs.insert_range(0..size);
            if stride != 0 {
                for dirty in (1..size).step_by(stride) { tree.remove(&dirty); runs.remove(&dirty); }
            }
            let a = || old(black_box(&tree), black_box(0..size));
            let b = || new(black_box(&runs), black_box(0..size));
            assert_eq!(a(), b());
            let mut first = Vec::new();
            let mut second = Vec::new();
            for round in 0..9 {
                if round % 2 == 0 { first.push(timed(a)); second.push(timed(b)); }
                else { second.push(timed(b)); first.push(timed(a)); }
            }
            first.sort_unstable();
            second.sort_unstable();
            println!("{size},{stride},{},{}", first[4], second[4]);
        }
    }
}
