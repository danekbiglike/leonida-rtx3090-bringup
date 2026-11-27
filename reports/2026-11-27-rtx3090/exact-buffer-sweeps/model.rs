//! Cache eviction model. Compile this file alongside the patched exact_sweep.rs.
//! Provenance: danekbiglike/rtx3090-20261127-exact-sweep.

mod exact_sweep;

use std::collections::BTreeMap;

#[derive(Clone, Copy, Default, PartialEq, Eq, Debug)]
struct Owners {
    list: bool,
    slot: bool,
}

type Entries = BTreeMap<u64, (Owners, u64)>;

#[derive(Default)]
struct Probes {
    arc: u64,
    com: u64,
}

impl Probes {
    fn held(&mut self, owners: &Owners) -> bool {
        self.arc += 1;
        if owners.list {
            return true;
        }
        self.com += 1;
        owners.slot
    }
}

fn compare(name: &str, seeded: u64, misses: u64, old_slot_owners: u64) {
    let mut original: Entries = (0..seeded)
        .map(|key| (key, (Owners { list: false, slot: key < old_slot_owners }, key + 1)))
        .collect();
    let mut patched = original.clone();
    let mut schedule = exact_sweep::Schedule::new();
    let mut eager = Probes::default();
    let mut gated = Probes::default();
    for key in seeded..seeded + misses {
        let now = key + 1;
        if original.len() >= 256 {
            original.retain(|_, (owners, used)| eager.held(owners) || *used + 512 > now);
        }
        schedule.prune(&mut patched, now, false, |owners| gated.held(owners));
        let entry = (Owners::default(), now);
        original.insert(key, entry);
        patched.insert(key, entry);
        assert_eq!(original, patched, "different survivors after miss {key}");
    }
    println!("danekbiglike/rtx3090-20261127-exact-sweep,{name},{seeded},{old_slot_owners},{misses},{},{},{},{},{}",
             original.len(), eager.arc, gated.arc, eager.com, gated.com);
}

fn main() {
    println!("report_id,model,seed_entries,old_com_owned,misses,final_entries,eager_arc_probes,patched_arc_probes,eager_com_pairs,patched_com_pairs");
    compare("recent", 256, 128, 0);
    compare("large_pinned", 4454, 716, 3942);
}

#[test]
fn mixed_hits_releases_and_new_owners_match_eager_eviction_at_every_request() {
    let mut original = Entries::new();
    let mut patched = Entries::new();
    let mut schedule = exact_sweep::Schedule::new();
    let mut seed = 97_u64;
    for now in 1..=7_000_u64 {
        seed = seed.wrapping_mul(6_364_136_223_846_793_005).wrapping_add(1);
        let owner_key = (seed >> 32) % 950;
        for map in [&mut original, &mut patched] {
            if let Some((owners, _)) = map.get_mut(&owner_key) {
                owners.list = (seed & 4) != 0;
                owners.slot = (seed & 2) != 0;
            }
        }
        let key = (seed >> 20) % 950;
        if let Some((_, used)) = original.get_mut(&key) {
            *used = now;
            patched.get_mut(&key).unwrap().1 = now;
        } else {
            if original.len() >= 256 {
                original.retain(|_, (v, used)| v.list || v.slot || *used + 512 > now);
            }
            schedule.prune(&mut patched, now, false, |v| v.list || v.slot);
            let entry = (Owners { list: seed & 16 != 0, slot: seed & 32 != 0 }, now);
            original.insert(key, entry);
            patched.insert(key, entry);
        }
        assert_eq!(original, patched, "request {now}");
    }
}
