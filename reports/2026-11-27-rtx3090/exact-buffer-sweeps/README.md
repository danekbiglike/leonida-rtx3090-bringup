# Avoid needless ownership checks for exact GPU buffer views

The Series X renderer can allocate a separate D3D12 buffer for a view whose first element does not align with the larger backing buffer. On a cache miss with at least 256 entries, the pinned VI-BR-PORT revision examines every cached view. For each entry held only by the map it calls D3D12 `AddRef` and `Release` even when a recent request already guarantees the entry must stay. A report on a different RTX 3080 system traced a heavy scene to this part of the renderer, with roughly 4,454 retained entries and 716 creations per frame. [Pinned implementation](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/shadow.rs#L5510) · [RTX 3080 report](https://github.com/Belobug/VIctory-Belobug-AMD/issues/346)

The [patch](exact-sweep.patch) preserves the original 512-request protection window. It checks age first. If all surviving entries are recent, it records the earliest time any could become eligible and skips scans until that request. New insertions and hits can only extend this interval for those entries. If even one old entry survives because a list or descriptor still owns it, the next eligible miss checks it again. On ordinary requests the cache retains the same buffers and bytes as the original policy. The scheduling state occupies two 64-bit words.

If a D3D12 allocation fails, the patch checks the whole cache once, including a cache under 256 entries. It frees only old entries with neither a list reference nor a descriptor reference and makes one more allocation attempt only if it actually released something. Recent and externally referenced resources remain protected. The renderer still creates new D3D12 resources for misses.

## Verification

| Synthetic workload | Misses | Eager COM reference probes | Patched probes | Final entries |
| --- | ---: | ---: | ---: | ---: |
| 256 recently used entries, all held only by the cache | 128 | 40,896 | 0 | 384 |
| 4,454 entries, including 3,942 older entries held by descriptors | 716 | 3,189,064 | 2,823,188 | 4,454 |

Each probe represents an `AddRef`/`Release` pair. The large case uses the size and miss count in the RTX 3080 report, plus an explicit assumption about descriptor ownership. The [model](model.rs) checks the full set of retained keys and their latest request after every miss. It counts operations on simulated owners. It does not measure driver time, live ownership or gameplay FPS. The [CSV](model.csv) includes the workload parameters. The earlier local RTX 3090 escort traces did not log the exact-buffer census.

Four tests in the patch cover expiry, both sides of the 512-request boundary, immediate rechecking of old owners, cleanup on allocation failure and counter rollover. An additional 7,000-request differential test includes hits, misses, newly held and released list/descriptor references. All five tests passed. An offline Windows x64 release check of the patched library and test targets passed with diagnostics enabled and rustc 1.98.1.

Apply the patch to `edsuuu/VI-BR-PORT` revision `2954325320735fa8b56a15e7f3e9654965e3462e`. To reproduce the model, copy `model.rs` and the patched `crates/victory-gpu/src/shadow/exact_sweep.rs` into a temporary directory, then run the following commands there.

```powershell
rustc --edition 2024 -O --test model.rs -o model-tests.exe
.\model-tests.exe --test-threads=1
rustc --edition 2024 -O model.rs -o model.exe
.\model.exe
```

Provenance ID `danekbiglike/rtx3090-20261127-exact-sweep` appears in the patch source, model and output. Local implementation and verification by the danekbiglike RTX 3090 bring-up project with ChatGPT. Credit to the VIctory and VI-BR-PORT maintainers for the underlying renderer and to the author of issue 346 for identifying this hotspot. Preserve the identifier and link the originating patch when reporting a derivative.
