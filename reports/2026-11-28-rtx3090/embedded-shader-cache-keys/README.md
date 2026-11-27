# Fix cache misses for embedded shader containers

The offline shader scanner used every byte from a DXBC header to the end of the containing file as its hash input. The same shader therefore acquired a different cache key when another record or a trailer followed it. The patch limits each raw input to the size in its DXBC header and validates that slice before returning it. Packed records retain their existing decoding. [Patch and synthetic regression](bound-raw-container.patch)

On a local 198,522,514-byte pipeline shader archive, all **19,106** corrected BLAKE3 hashes matched the 32-byte fingerprints stored with their records. The containers totalled 197,815,592 bytes. Summing the previous tail lengths at the same 19,106 offsets gives 1,803,207,601,877 bytes per hash pass. That last figure is a calculation from offsets. No terabyte-scale benchmark was run. The one-pass measurement used a small Rust harness containing the patched scanner and the same project libraries.

The synthetic test checks two distinct 32-byte containers, separated by padding and followed by a trailer and a truncated magic number. Both embedded hashes must match the standalone hashes. It passed. The preimage Git blob for `apps/victory/src/shader.rs` was `1c2028546e2980625fd10d105eff5e540f2750ce`. The patch also passed `git apply --check` against that version.

This affects offline warming of raw containers embedded in larger files. There is no gameplay FPS measurement for this change. Only code and aggregate counts are included.
