use std::{hint::black_box, time::Instant};

fn main() {
    println!("pattern,repeat,reference_ns,indexed_ns,output_ranges");
    for (name, size, repeats) in [("world", 1700, 12), ("small", 27, 4), ("write-heavy", 811, 7)] {
        let mut events = Vec::new();
        let mut index = ByCopy::default();
        let mut keys = Vec::new();
        let mut seed = 1337u32;
        for n in 0..size * repeats {
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            let key = 0x100000 + ((seed >> 8) as usize % size) * 64;
            let from = ((seed >> 5) & 0xffff) as usize;
            let mut refresh = || {
                let id = keys.len();
                index.entry(key).or_insert_with(|| { keys.push(key); id });
                Touch::Refresh(key, from, from + 48)
            };
            if n % 1151 == 0 { events.push(Touch::Part); }
            if n % (if name == "write-heavy" { 2 } else { 13 }) == 0 {
                events.push(Touch::Write(key));
            } else {
                events.extend([refresh(), refresh()]);
            }
        }
        let mut scratch = indexed::FrontRanges::default();
        let mut run = || {
            scratch.begin(keys.len());
            let mut previous = None;
            for event in &events {
                let key = match *event {
                    Touch::Refresh(k, ..) | Touch::Write(k) => k,
                    Touch::Part => { scratch.next_part(); continue; }
                    _ => continue,
                };
                let id = match previous {
                    Some((last, id)) if last == key => id,
                    _ => {
                        let Some(&id) = index.get(&key) else { continue };
                        previous = Some((key, id));
                        id
                    }
                };
                match *event {
                    Touch::Refresh(_, from, to) => scratch.refresh(id, from, to),
                    _ => scratch.write(id),
                }
            }
            scratch.ranges().map(|(i,a,b)| (keys[i],a,b)).collect::<Vec<_>>()
        };
        let expected = front_spans(events.iter().copied());
        assert_eq!(expected, run());
        let rounds = if size < 100 { 1000 } else { 20 };
        for repeat in 0..14 {
            let mut times = [0; 2];
            for method in [repeat % 2, 1 - repeat % 2] {
                let start = Instant::now();
                for _ in 0..rounds {
                    if method == 0 { black_box(front_spans(black_box(&events).iter().copied())); }
                    else { black_box(run()); }
                }
                times[method] = start.elapsed().as_nanos() / rounds;
            }
            println!("{name},{repeat},{},{},{}", times[0], times[1], expected.len());
        }
    }
}
