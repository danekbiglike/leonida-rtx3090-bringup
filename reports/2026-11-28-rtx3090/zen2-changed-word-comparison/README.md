# Finding changed words on a Ryzen 7 3700X

Two hot buffer paths can use VIctory's existing AVX2 comparison for aligned data. This is the same substitution proposed in upstream PR 145. The table shows an independent local measurement of the two comparison routines at the same alignment on a Ryzen 7 3700X. [Upstream PR 145](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/145) · [Benchmark and call sites](zen2-benchmark.patch)

| Input page | Scalar, µs | Vector path, µs |
| --- | ---: | ---: |
| Unchanged | 79.40 | 72.95 |
| A changed byte every 541 bytes | 250.20 | 126.40 |
| A changed byte every 12 bytes | 7293.55 | 1125.20 |
| One contiguous change | 905.10 | 88.40 |

Each entry is the median of 12 batches. A batch compares the same pair of 64 KiB pages 64 times with warm caches. The order of the scalar and vector runs alternated every round. The benchmark checked the exact offsets and lengths of every returned range for all 16 combinations of start and end alignment for each input shape. The randomized existing comparison test passed too. The accompanying RTX 3090 striped-buffer readback test verified all 10 MiB after each of three refreshes. [All 96 timings and output counts](page-comparisons.csv)

The speedup depends on the input and covers only comparison and building its output ranges. These timings do not include moving or mapping pages, rendering a frame or waiting for workers. They cannot predict the FPS change or establish a fix for the multi-second streaming stall.
