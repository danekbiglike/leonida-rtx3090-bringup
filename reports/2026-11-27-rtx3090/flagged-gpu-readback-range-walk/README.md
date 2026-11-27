# Walk the flagged GPU readback pieces once per declared range

The readback planner previously searched its sorted flags once for every declared 64 KiB piece. The patch finds the start of each declaration once, then visits just its flagged pieces in their existing order. Flags remain shared across overlapping declarations. The original donor copy, texture quality, fencing and ordering are preserved. The implementation targets the original per-piece binary search in VI-BR-PORT.

On a Ryzen 7 3700X, 8,192 declared pieces in 128 overlapping ranges with approximately 20% flagged took a median of 219.921 microseconds per iteration with per-piece lookup and 5.883 microseconds with range lookup. Twelve rounds alternated the order of the two selectors. Each round repeated an iteration 250 times and both selectors produced the same checksum. A separate renderer was loading a scene. These measurements cover CPU selection work only.

The harness compared results for 40,000 randomized declarations and a range ending at the maximum 32-bit index. The accompanying in-tree regression test also covers empty ranges, different copy owners and duplicate or conflicting flags. To run the standalone test, apply the patch and run `python verify.py path/to/crates/victory-gpu/src/host.rs path/to/rustc` with a Windows x64 Rust toolchain. The harness extracts the implementation directly from that file.

Patch and measurements by danekbiglike with ChatGPT, 27 November 2026. Provenance marker danekbiglike/rtx3090-20261127-flagged-range. Gameplay is measured separately.
