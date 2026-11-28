# RTX 3090 host preparation: reusing the submission's shadow index

The November 28 4K cell trace recorded about ten thousand buffer refreshes in one late gameplay frame. Its submitting thread reported 57.2 ms of preparation and 19.0 ms of refresh work. Those totals include substantially more work than constructing the refresh intervals. [4K gameplay measurement](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/41dbb3cd91f46d4a965c6040f26cbf51f7603a29/reports/2026-11-28-rtx3090/nvidia-4k-prison-cell)

The changed planner walks the submission's recorded commands once using the existing index from shadow address to slot. It reuses two vectors between submissions and retains the original order of first appearance. A shader write blocks additional refreshes for that shadow in the current part. A later part can extend the range again. Writes to shadows with no refresh anywhere in the submission have no output interval. [Source and equivalence test](indexed-front-ranges.patch)

| Synthetic input | Original planner | Indexed planner |
| --- | ---: | ---: |
| 1,700 possible shadows, mixed repeated refreshes | 363.37 µs | 254.94 µs |
| 27 possible shadows | 2.388 µs | 1.276 µs |
| 811 possible shadows, frequent writes | 56.02 µs | 45.53 µs |

Times are medians of fourteen paired trials on the Ryzen 7 3700X. The test alternates execution order. The original receives a prebuilt list of touches. The new version receives the existing address index. Both return newly allocated result vectors and the harness compares every output interval and its order. The larger mixed input saved 108.43 µs per synthetic call. This measures one CPU operation. Game frame times depend on other work as well. [Paired observations](planning.csv)

The integrated renderer passed the four host planning tests, including 140,000 operations comparing both planners over repeated resets. The local Windows build also passed 47 descriptor, 23 guest-memory, 26 input and one head-map priority test. Two other tests are ignored by default. The head-map priority change is a separate contribution in [VIctory-NVIDIA pull request 703](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/703).

To reproduce, apply the patch to revision 63b902fe1720a5188ee79d94a88c8de0470f6349. Run the following in the report folder using the patched checkout path. The benchmark uses the same interval planner as the renderer.

```powershell
git -C C:\src\VIctory-NVIDIA apply (Resolve-Path indexed-front-ranges.patch)
python prepare.py C:\src\VIctory-NVIDIA bench.rs
rustc --edition=2024 -A dead_code -C opt-level=3 -C target-cpu=znver2 bench.rs -o bench.exe
.\bench.exe
```

Measured by danekbiglike with ChatGPT on 28 November 2026.
