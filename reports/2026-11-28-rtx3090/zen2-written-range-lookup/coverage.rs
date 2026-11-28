/// The ranges that were actually queried. Each answer must be covered by a
/// single query, even if two adjacent or overlapping queries span it together.
#[derive(Default)]
pub(super) struct Coverage(Vec<(usize, usize)>);

impl Coverage {
    const LINEAR: usize = 8;

    pub(super) const fn new() -> Self { Self(Vec::new()) }
    pub(super) fn clear(&mut self) { self.0.clear(); }
    pub(super) fn len(&self) -> usize { self.0.len() }

    pub(super) fn with_extra(mut self, extra: Vec<(usize, usize)>) -> Self {
        if extra.is_empty() { return self; }
        self.0.extend(extra);
        Self::from_ranges(self.0)
    }

    pub(super) fn from_ranges(mut spans: Vec<(usize, usize)>) -> Self {
        if spans.len() > Self::LINEAR {
            spans.sort_unstable_by(|a, b| a.0.cmp(&b.0).then_with(|| b.1.cmp(&a.1)));
            let mut end = None;
            spans.retain(|&(_, b)| {
                if end.is_some_and(|last| last >= b) { return false; }
                end = Some(b);
                true
            });
        }
        Self(spans)
    }

    pub(super) fn covers(&self, first: usize, last: usize) -> bool {
        if self.0.len() <= Self::LINEAR {
            return self.0.iter().any(|&(a, b)| a <= first && last <= b);
        }
        // The retained ends increase. The last eligible start therefore
        // has the largest end among all ranges that can cover the request.
        let count = self.0.partition_point(|&(start, _)| start <= first);
        count > 0 && last <= self.0[count - 1].1
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn containment_agrees_with_individual_kernel_queries() {
        let mut seed = 17u32;
        let mut pick = || {
            seed = seed.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
            (seed >> 16) as usize
        };
        for n in [0, 1, 7, 8, 9, 64, 200] {
            for _ in 0..10 {
                let spans: Vec<_> = (0..n).map(|_| {
                    let a = pick() % 64;
                    (a, a + 1 + pick() % 12)
                }).collect();
                let indexed = Coverage::from_ranges(spans.clone());
                for a in 0..76 {
                    for b in a..77 {
                        assert_eq!(indexed.covers(a,b), spans.iter().any(|&(x,y)| x <= a && b <= y));
                    }
                }
            }
        }
        let many: Vec<_> = (0..100).map(|i| (2*i, 2*i+3)).collect();
        assert!(!Coverage::from_ranges(many).covers(1, 4));
    }
}
