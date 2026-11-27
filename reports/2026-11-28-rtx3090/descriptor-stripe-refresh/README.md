# Active descriptor slots grouped by refresh pass on the Ryzen 7 3700X

The bindless buffer sweep already refreshes a sixteenth of its descriptor slots on each round. This change stores the active slots of each of those sixteen parts together. To forget a part, it drains that part's vector and clears only the indices it touched. The source of each range, the number of slots considered per refresh round, texture resolution and shader math are unchanged. The baseline for this experiment is the dense active-slot implementation proposed in [VIctory-NVIDIA PR 448](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/448).

On the Ryzen 7 3700X the median time to forget and repopulate one stripe was 0.149 ms for that baseline and 0.087 ms with this change, a reduction of 0.061 ms (41.2%). The harness both clears and repopulates one-sixteenth of 81,109 active slots spread across 740,003 locations. It executes 96 passes per measurement and alternates the order of the two versions in twelve paired measurements. All final checksums matched. These are descriptor bookkeeping times with synthetic slots. They cannot be converted into a gameplay FPS improvement. [All measurements](stripe-bench.csv)

The renderer's test also compares the collection to a BTreeMap over 97 rounds of overwrites, removals, stripe refresh and complete reset. Both heap-range correctness tests passed on Windows. One existing benchmark is ignored by default.

## Reproduce

Check out commit bf8f3dc0b8cc71458f227b60486f8f88557255dd from the linked PR. Apply the included patch in that checkout. With Python 3 and Rust for Windows x64 on PATH, run the following from the report directory. Replace the checkout path with your chosen path.

```powershell
git -C C:\src\VIctory-NVIDIA apply (Resolve-Path partition-by-pass.patch)
python prepare-stripe-bench.py .\bench C:\src\VIctory-NVIDIA
rustc --edition 2024 -Awarnings -C opt-level=3 -C target-cpu=znver2 .\bench\main.rs -o .\bench\measure.exe
.\bench\measure.exe
```

The patch applied cleanly to the named commit. Local implementation, regression coverage and measurements by danekbiglike with ChatGPT, 28 November 2026.
