# Keeping clean guest-memory blocks in ranges on Ryzen 7 3700X

The RTX 3090 paired-lighting renderer checks which 64 KiB guest-memory blocks need refreshing before updating host buffers. The previous path copied every clean block number in the queried range into a temporary vector, even when nothing had changed. The patch stores adjacent clean blocks together and snapshots just the gaps for each query. The existing code decides which dirty or unmapped blocks to protect and when to report them written. Taking a snapshot preserves the iteration order when guarding another view of the same memory changes the set. [Renderer patch](clean-block-ranges.patch)

For a synthetic 174 MiB range, looking up unchanged blocks took **6,031 ns before and 16 ns after**. With one dirty block in 97 it took 9,377 ns before and 378 ns after. Alternating dirty and clean blocks reversed the result, from 5,502 ns to 6,253 ns. The benchmark times identifying changed blocks, excluding Windows protection changes, GPU work and copying payload bytes. It alternates measurement order and reports the median of nine batches of 1,000 scans. A separate release build was running on the machine. [All twelve workloads](guard-scan.csv) · [Benchmark source](bench_guards.rs)

The Windows release build passed 57 selected tests across memory, input, descriptors and write watching. One existing event-log test was skipped by its own test annotation. A seeded regression inside the patch ran 20,000 iterations against the previous block-by-block representation, checking membership and the returned gaps after inserts, removals and range merges. Game FPS and the effect on visible artifacts remain to be measured for this binary. [Test results](tests.txt)

To rerun the isolated lookup benchmark on this CPU, place `bench_guards.rs` and `clean_blocks.rs` together and run `rustc --edition 2024 -O -C target-cpu=znver2 bench_guards.rs`, then run the resulting executable. [Range implementation](clean_blocks.rs)

Measured by danekbiglike with ChatGPT on 28 November 2026. Ryzen 7 3700X, 32 GiB RAM. Renderer SHA-256 `c006e8cf6bb99eef531f7c3ee778b37fca8615d7329eeb7cc06f3be414e3a5ad`.
