//! Compare retained Rust allocation requests for the old and patched diagnostics.
//! Copy this file next to the patched placed_filler.rs before compiling.
//! Data ID: danekbiglike/rtx3090-20261127-placed-filler.

mod placed_filler;

use std::alloc::{GlobalAlloc, Layout, System};
use std::collections::BTreeSet;
use std::sync::atomic::{AtomicUsize, Ordering};

struct CountRequestedBytes;
static LIVE: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for CountRequestedBytes {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = unsafe { System.alloc(layout) };
        if !ptr.is_null() {
            LIVE.fetch_add(layout.size(), Ordering::Relaxed);
        }
        ptr
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        LIVE.fetch_sub(layout.size(), Ordering::Relaxed);
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static ALLOCATOR: CountRequestedBytes = CountRequestedBytes;

// Diagnostic accounting from texture_at at 29543253. Its BTreeSet persists
// for the process. The mutex used there has no Rust heap allocation.
#[derive(Default)]
struct Original {
    raw: BTreeSet<(u64, [u32; 14])>,
    twins: usize,
}

impl Original {
    fn record(&mut self, address: u64, normalized: &[u32; 14], raw: &[u32; 14]) {
        if raw == normalized || !self.raw.insert((address, *raw)) {
            return;
        }
        let group = (address, [0; 14])..=(address, [u32::MAX; 14]);
        let matching = self.raw.range(group).filter(|(_, variant)| {
            let mut key = *variant;
            key[1] = 0;
            key[13] = 0;
            key == *normalized
        });
        if matching.count() > 1 {
            self.twins += 1;
        }
    }
}

const DESCRIPTORS: u32 = 262_144;
const REPORT_ID: &str = "danekbiglike/rtx3090-20261127-placed-filler";

fn main() {
    let mode = std::env::args().nth(1).expect("pass original, default, or opt-in");
    assert!(matches!(&*mode, "original" | "default" | "opt-in"));
    let mut original = Original::default();
    let before = LIVE.load(Ordering::Relaxed);
    for index in 0..DESCRIPTORS {
        let address = u64::from(index / 256) << 16;
        let mut normalized = [0; 14];
        normalized[3] = 64 << ((index / 32) % 8);
        let mut raw = normalized;
        raw[1] = 1 + index % 32;
        // Visit the same descriptor twice to exercise duplicate handling.
        for _ in 0..2 {
            if mode == "original" {
                original.record(address, &normalized, &raw);
            } else {
                placed_filler::record(address, &normalized, &raw);
            }
        }
    }
    let (keys, twins) = if mode == "original" {
        (original.raw.len(), original.twins)
    } else {
        let snapshot = placed_filler::snapshot();
        assert_eq!(snapshot.is_some(), mode == "opt-in");
        snapshot.unwrap_or_default()
    };
    let retained = LIVE.load(Ordering::Relaxed) - before;
    let expected_keys = match mode.as_str() {
        "original" => DESCRIPTORS as usize,
        "default" => 0,
        _ => placed_filler::MAX_KEYS,
    };
    assert_eq!(keys, expected_keys);
    assert_eq!(twins, keys - keys / 32);
    println!("{REPORT_ID},{mode},{},{keys},{twins},{retained}", DESCRIPTORS * 2);
    std::hint::black_box(original);
}
