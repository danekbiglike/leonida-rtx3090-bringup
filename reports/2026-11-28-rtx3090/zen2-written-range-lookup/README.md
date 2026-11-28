# Checking queried page ranges on the Ryzen 7 3700X

In the measured 4K prison route, VIctory's submission thread spent a median 6.5 ms per frame asking which CPU pages had been written. This candidate changes one part of that work. It indexes the memory ranges already queried and skips traversing buffer candidates while the current write information is held. On the Ryzen 7 3700X, a synthetic batch of 5,500 membership checks against 128 ranges took a median of **50.4 µs**, down from **593.9 µs**. The game also spends time making the actual kernel queries. [Gate measurements](../4k-prison-ordered-uploads) · [Production patch](coverage.patch)

| Ranges in the batch | Original scan, µs | Candidate, µs |
| ---: | ---: | ---: |
| 4 | 38.1 | 47.2 |
| 8 | 92.2 | 90.3 |
| 16 | 140.9 | 29.0 |
| 32 | 238.7 | 37.3 |
| 128 | 593.9 | 50.4 |
| 512 | 3,138.7 | 68.9 |

Each row is the median of 12 repetitions of the same generated query set, with timing order alternated. Candidate timings include copying the source vector and building the index. The original scan reads the existing vector directly. The four-range case was slower. The generated ranges and hit rates are synthetic. These measurements do not establish an improvement in game FPS. [Raw timings](range-lookup.csv) · [Benchmark](range-lookup-bench.rs)

Queries still require containment by a single original range. An adjacent or partly overlapping range cannot acknowledge bytes on its neighbor's behalf. An exhaustive comparison on generated overlapping sets checks the indexed answer against the original scan. Separate tests verify that additional page writes remain observable, that a held journal avoids traversing the candidate iterator, and that three RTX 3090 buffer ordering probes pass on this build. [Test results](tests.txt) · [Lookup implementation](coverage.rs) · [GPU probe details](../rtx3090-deferred-copy-ordering)

To reproduce the standalone timings with native Rust on Windows, set `COVERAGE_SOURCE` to the absolute path of the included `coverage.rs` and run `rustc --edition 2024 -C opt-level=3 -C target-cpu=znver2 range-lookup-bench.rs`. Run the resulting executable with the renderer closed. The supplied patch was checked against our row-copy build with upstream PR 874 applied.
