
use std::hint::black_box;
use std::time::Instant;

fn next(state: &mut u64) -> u32 {
    *state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
    (*state >> 32) as u32
}

fn main() {
    let mut state = 3090;
    let mut checks = 0;
    for _ in 0..500 {
        let raw: Vec<_> = (0..512).map(|_| ((next(&mut state) % 8) as usize,
                                            next(&mut state) % 320, next(&mut state) % 3 != 0)).collect();
        let pieces = flagged_pieces(&raw);
        for _ in 0..80 {
            let owner = (next(&mut state) % 9) as usize;
            let first = next(&mut state) % 340;
            let count = next(&mut state) % 140;
            let reference: Vec<_> = (0..count).filter(|i| pieces.binary_search(&(owner, first + i)).is_ok()).collect();
            assert_eq!(flagged_in_range(&pieces, owner, first, count).collect::<Vec<_>>(), reference);
            checks += 1;
        }
    }
    assert_eq!(flagged_in_range(&[(4, u32::MAX)], 4, u32::MAX - 1, 2).collect::<Vec<_>>(), [1]);
    println!("{checks} differential checks and upper-bound check passed");

    // 8,192 declared pieces across 128 ranges, about one fifth flagged.
    let ranges: Vec<_> = (0..128u32).map(|i| ((i % 16) as usize, (i / 16) * 60, 64u32)).collect();
    let raw: Vec<_> = ranges.iter().flat_map(|&(owner, first, len)| {
        (0..len).map(move |i| (owner, first + i, (owner as u32 + first + i) % 5 == 0))
    }).collect();
    let flagged = flagged_pieces(&raw);
    let mut samples = [vec![], vec![]];
    let mut reference_sum = None;
    for round in 0..12 {
        for algorithm in [round % 2, (round + 1) % 2] {
            let start = Instant::now();
            let mut total = 0u64;
            for _ in 0..250 {
                let keys = black_box(&flagged);
                for &(owner, first, count) in black_box(&ranges) {
                    if algorithm == 0 {
                        for offset in 0..count {
                            if keys.binary_search(&(owner, first + offset)).is_ok() {
                                total += u64::from(offset) + 1;
                            }
                        }
                    } else {
                        for offset in flagged_in_range(keys, owner, first, count) {
                            total += u64::from(offset) + 1;
                        }
                    }
                }
            }
            let micros = start.elapsed().as_secs_f64() * 1e6 / 250.0;
            samples[algorithm].push(micros);
            assert_eq!(*reference_sum.get_or_insert(black_box(total)), total);
        }
    }
    for (name, times) in ["per_piece", "per_range"].iter().zip(&mut samples) {
        times.sort_by(|a,b| a.total_cmp(b));
        println!("{name} median_us {:.3}", (times[5] + times[6]) / 2.0);
    }
}
