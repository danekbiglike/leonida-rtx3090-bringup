use std::collections::BTreeMap;
use std::ops::Range;

/// Disjoint, non-adjacent half-open ranges of clean 64 KiB blocks.
pub(super) struct CleanBlocks(BTreeMap<usize, usize>);

impl CleanBlocks {
    pub(super) const fn new() -> Self {
        Self(BTreeMap::new())
    }

    pub(super) fn contains(&self, block: &usize) -> bool {
        self.0
            .range(..=block)
            .next_back()
            .is_some_and(|(_, end)| block < end)
    }

    pub(super) fn insert(&mut self, block: usize) {
        self.insert_range(block..block + 1);
    }

    pub(super) fn insert_range(&mut self, mut range: Range<usize>) {
        if range.is_empty() {
            return;
        }
        if let Some((&start, &end)) = self.0.range(..=range.start).next_back()
            && end >= range.start
        {
            if end >= range.end {
                return;
            }
            self.0.remove(&start);
            range.start = start;
        }
        while let Some((&start, &end)) = self.0.range(range.start..=range.end).next() {
            self.0.remove(&start);
            range.end = range.end.max(end);
        }
        self.0.insert(range.start, range.end);
    }

    pub(super) fn remove(&mut self, block: &usize) {
        if let Some((&start, &end)) = self.0.range(..=block).next_back()
            && *block < end
        {
            self.0.remove(&start);
            if start < *block {
                self.0.insert(start, *block);
            }
            if *block + 1 < end {
                self.0.insert(*block + 1, end);
            }
        }
    }

    /// Snapshot only the gaps. Guarding an alias can mutate the set as the caller walks them.
    pub(super) fn missing(&self, range: Range<usize>) -> Vec<Range<usize>> {
        let mut gaps = Vec::new();
        if range.is_empty() {
            return gaps;
        }
        let mut cursor = range.start;
        if let Some((_, &end)) = self.0.range(..range.start).next_back() {
            cursor = cursor.max(end);
        }
        if cursor >= range.end {
            return gaps;
        }
        for (&start, &end) in self.0.range(range.start..range.end) {
            if cursor < start {
                gaps.push(cursor..start);
            }
            cursor = end;
        }
        if cursor < range.end {
            gaps.push(cursor..range.end);
        }
        gaps
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    #[test]
    fn gaps_match_individual_clean_blocks_after_splits_joins_and_alias_writes() {
        let mut ranges = CleanBlocks::new();
        let mut blocks = BTreeSet::new();
        let mut seed = 15_u64;
        let mut draw = |n: usize| {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
            ((seed >> 32) as usize) % n
        };
        for _ in 0..20_000 {
            let start = draw(300);
            let end = start + draw(50);
            match draw(4) {
                0 => {
                    ranges.insert_range(start..end);
                    blocks.extend(start..end);
                }
                1 => {
                    ranges.insert(start);
                    blocks.insert(start);
                }
                _ => {
                    ranges.remove(&start);
                    blocks.remove(&start);
                }
            }
            let first = draw(310);
            let last = first + draw(70);
            assert_eq!(ranges.contains(&first), blocks.contains(&first));
            let expected: Vec<_> = (first..last).filter(|b| !blocks.contains(b)).collect();
            let gaps = ranges.missing(first..last);
            assert!(gaps.windows(2).all(|r| r[0].end < r[1].start));
            assert_eq!(gaps.into_iter().flatten().collect::<Vec<_>>(), expected);
        }
    }
}
