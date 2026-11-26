# Buffer descriptor bookkeeping on a Ryzen 7 3700X

UwUCammie’s [buffer descriptor bitsets](https://github.com/fxceless/victory-fork/pull/1190) reduced CPU time in the dense bookkeeping workload on our Windows machine. This port handles our renderer’s batched descriptor writes under the existing lock. The set of slots returned by the renderer is preserved. Shader, lighting and texture settings stay at their previous values.

| CPU workload | Previous sets | Bitsets | Repeat with previous sets | Repeat with bitsets |
| --- | ---: | ---: | ---: | ---: |
| 43,000 writes/frame, 16 frames | 139.736 ms | 6.823 ms | 95.542 ms | 4.622 ms |
| 16 writes/frame, 48 frames | 1.432 ms | 0.971 ms | 0.750 ms | 0.546 ms |

Each number is the median *total* time for one complete workload over eight alternating pairs following warm-up. The repeat saved about 5.68 ms per synthetic dense frame. All paired checksums matched, and 32 renderer descriptor tests passed. The first run overlapped compilation on the same PC. Absolute timings varied between runs. These experiments time CPU data structures with synthetic slot updates. A gameplay FPS gain remains to be measured. [All 64 measurements](slot-bitsets/cpu-pairs.csv)

## Reproduce

Prepare the source from the [heap-owner escort](heap-owner-escort.md). Apply [the batched texture lookup patch](../../patches/victory-batch-texture-remaps.patch), then [the descriptor bitset port](../../patches/victory-buffer-slot-bitsets.patch). The lookup patch has an opt-in diagnostic that compares both algorithms against the same live descriptor table. The CPU benchmark below only exercises the slot sets.

Build and test with Rust 1.98.1 on Windows:

```powershell
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib descriptor:: -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
```

Use the [original benchmark driver and Rust workload at the measured revision](https://github.com/UwUCammie/victory-amd/tree/7df67bc2c645aaf973c293c61a292543f91ca55e/benchmarks). The driver reads the SlotSet implementation from a git revision. Commit the prepared renderer changes on a local branch, then run `python PATH/TO/benchmarks/slot_sets.py HEAD` from that checkout. We compiled the same SlotSet text from the working tree with the pinned Rust workload (`rustc --edition=2024 -O`). The benchmark source SHA-256 was `69b40b5fb404ee8c634792a7185b60f942865d15091eca84a3f5bf7c33d72353`. The combined Windows executable had SHA-256 `62a5bfdd336d99b0626dd8ed3c285bb85ca31a6eeb387d517715cfea5b7ba66f`. Credit for the original bitset implementation and benchmark belongs to UwUCammie.
