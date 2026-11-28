use std::hint::black_box;
use std::time::Instant;

macro_rules! workload {
    () => {
        pub fn seeded(len: u32, seed: u32, repeated: u32) -> TextureQueue {
            let mut queue = TextureQueue::default();
            for i in 0..len {
                let index = i.wrapping_mul(747796405).wrapping_add(seed);
                let bits = index.wrapping_mul(2891336453).rotate_right(7);
                let written = u64::from(bits % 1024);
                let again = bits % 100 < repeated;
                queue.slots.insert(index, Waiting {
                    due: u64::from(bits.rotate_right(13) % 40),
                    written, write: u64::from(i) + 1,
                    looks: u8::from(again && bits & 1 == 0),
                    mapped: u64::from(again && bits & 1 != 0),
                    checked: (0, 0, 0, 0, 0),
                });
            }
            queue
        }
    }
}

type Order = (Vec<(u32, u64)>, [u64; 5]);
mod before {
    include!("before.rs");
    workload!();
    pub fn snapshot(queue: &TextureQueue, frame: u64, max: usize) -> super::Order {
        (if max == 0 { Vec::new() } else { queue.due(frame, max) }, queue.census(frame))
    }
}
mod after {
    include!("after.rs");
    workload!();
    pub fn snapshot(queue: &TextureQueue, frame: u64, max: usize) -> super::Order {
        let (ready, census) = queue.ready(frame, max != 0);
        (ready.order(max), census)
    }
}
fn main() {
    let mut comparisons = 0;
    for n in [0, 1, 9, 81, 257] {
        for repeat in [0, 10, 50, 90, 100] {
            let a = before::seeded(n, 71, repeat);
            let b = after::seeded(n, 71, repeat);
            for frame in [0, 10, 80] {
                for limit in [0, 1, 2, 7, 16, 30, 99, 257, usize::MAX] {
                    assert_eq!(before::snapshot(&a, frame, limit), after::snapshot(&b, frame, limit));
                    comparisons += 1;
                }
            }
        }
    }
    eprintln!("identical orders and censuses: {comparisons}");
    if std::env::args().any(|arg| arg == "--check") { return; }
    println!("entries,repeat_percent,limit,pair,original_us,new_us");
    for (size, repeat, limit) in [(13_498, 50, 4096), (30_000, 75, 4096), (32, 50, 4096)] {
        let a = before::seeded(size, 199, repeat);
        let b = after::seeded(size, 199, repeat);
        assert_eq!(before::snapshot(&a, 27, limit), after::snapshot(&b, 27, limit));
        let measure = |new: bool| {
            let now = Instant::now();
            for _ in 0..100 {
                let result = if new { after::snapshot(black_box(&b), 27, limit) }
                             else { before::snapshot(black_box(&a), 27, limit) };
                black_box(result);
            }
            now.elapsed().as_secs_f64() * 1e4
        };
        measure(false);
        measure(true);
        for i in 0..10 {
            let (old, new) = if i % 2 == 0 { (measure(false), measure(true)) }
                             else { let new = measure(true); (measure(false), new) };
            println!("{size},{repeat},{limit},{i},{old:.3},{new:.3}");
        }
    }
}
