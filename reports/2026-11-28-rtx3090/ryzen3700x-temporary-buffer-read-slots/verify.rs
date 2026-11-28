use std::collections::{HashMap, HashSet};
use std::hash::BuildHasherDefault;
use std::hint::black_box;
use std::time::Instant;

include!("first_read_at.rs");
include!("address_hash.rs");

type Key = (usize, usize, usize, u32);
type Places = HashMap<Key, usize, BuildHasherDefault<AddressHash>>;

fn main() {
    println!("operations,distinct_keys,paired_round,reference_ns,slot_ns");
    for (count, key_count) in [(0, 0), (32, 19), (4800, 530), (4800, 4700)] {
        let mut places = Places::default();
        let mut operations = Vec::new();
        let mut end = 0usize;
        let mut state = 0x8c75_4201u32;
        for i in 0..count {
            state = state.wrapping_mul(1664525).wrapping_add(1013904223);
            let n = (state as usize >> 8) % key_count;
            let key = (n / 13, (n / 4) * 128, 37 + 64 * (n % 7), (n % 4) as u32);
            let at = *places.entry(key).or_insert_with(|| {
                let offset = end;
                end = (end + key.2).next_multiple_of(256);
                offset
            });
            if i % 13 != 0 {
                operations.push((key, at));
            }
        }
        operations.sort_by_key(|(key, _)| key.3);
        let mut seen = HashSet::new();
        let expected: Vec<_> = operations.iter().map(|(key, _)| seen.insert(*key)).collect();
        let mut bits = vec![0; end.div_ceil(256 * 64)];
        let actual: Vec<_> = operations.iter().map(|(_, at)| first_read_at(&mut bits, *at as u64)).collect();
        assert_eq!(actual, expected);
        let mut last_slot = vec![0; (4 << 20) / (256 * 64)];
        assert!(first_read_at(&mut last_slot, (4 << 20) - 256));
        assert!(!first_read_at(&mut last_slot, (4 << 20) - 256));
        for round in 0..31 {
            let mut table = places.clone();
            let mut old = || {
                let start = Instant::now();
                let emitted = black_box(&operations).iter().filter(|(key, _)| table.remove(key).is_some()).count();
                (start.elapsed().as_nanos(), emitted)
            };
            let new = || {
                let start = Instant::now();
                let mut bits = vec![0; end.div_ceil(256 * 64)];
                let emitted = black_box(&operations).iter().filter(|(_, at)| first_read_at(&mut bits, *at as u64)).count();
                (start.elapsed().as_nanos(), emitted)
            };
            let (before, after) = if round % 2 == 0 { (old(), new()) } else {
                let after = new();
                (old(), after)
            };
            assert_eq!(before.1, expected.iter().filter(|&&b| b).count());
            assert_eq!(after.1, before.1);
            println!("{count},{},{round},{},{}", places.len(), before.0, after.0);
        }
    }
}
