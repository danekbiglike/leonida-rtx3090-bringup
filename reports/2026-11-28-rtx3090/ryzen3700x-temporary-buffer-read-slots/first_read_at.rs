fn first_read_at(words: &mut [u64], offset: u64) -> bool {
    debug_assert_eq!(offset % 256, 0);
    let slot = (offset / 256) as usize;
    let bit = 1u64 << (slot % 64);
    let word = &mut words[slot / 64];
    let first = *word & bit == 0;
    *word |= bit;
    first
}
