use std::hint::black_box;
use std::time::Instant;

// Compile the two production implementations side by side. The extraction
// script supplies only HeapRanges and HEAP_ROUND from each renderer revision.
mod flat { include!("flat.rs"); }
mod striped { include!("striped.rs"); }

const SLOTS: u32 = 740_003;
const ACTIVE: u32 = 81_109;
const PASSES: u32 = 96;

macro_rules! run {
    ($name:ident) => {{
        let mut ranges = $name::HeapRanges::default();
        let mut by_stripe: [Vec<u32>; 16] = Default::default();
        for i in 0..ACTIVE {
            let slot = ((u64::from(i) * 104_729) % u64::from(SLOTS)) as u32;
            by_stripe[slot as usize % 16].push(slot);
            ranges.set(slot, Some((slot, 0, 16)));
        }
        let started = Instant::now();
        for pass in 0..PASSES {
            let part = pass % 16;
            $name::forget(&mut ranges, part);
            for &slot in &by_stripe[part as usize] {
                ranges.set(slot, Some((slot, u64::from(pass), 16)));
            }
            black_box(&ranges);
        }
        let elapsed = started.elapsed().as_secs_f64() * 1000.0 / f64::from(PASSES);
        let sum = ranges.ranges().map(|r| u64::from(r.0) + r.1).sum::<u64>();
        (elapsed, sum)
    }};
}

fn main() {
    println!("order,flat_ms_per_pass,striped_ms_per_pass,checksum");
    for i in 0..12 {
        let (flat, striped) = if i % 2 == 0 {
            (run!(flat), run!(striped))
        } else {
            let striped = run!(striped);
            (run!(flat), striped)
        };
        assert_eq!(flat.1, striped.1);
        println!("{i},{:.6},{:.6},{}", flat.0, striped.0, flat.1);
    }
}
