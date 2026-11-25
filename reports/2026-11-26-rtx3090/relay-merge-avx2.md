# AVX2 merge of GPU writes into game memory on Ryzen 7 3700X

This optional CPU patch skips 32-byte blocks whose GPU contents match the saved reference. When any bytes changed, it merges the device changes into the latest CPU copy, preserving bytes the game alone wrote. It refreshes the reference even if the game already holds the value the GPU wrote. Short inputs and processors without AVX2 use the original implementation. The runtime switch defaults off. [Renderer patch](../../patches/victory-relay-merge-avx2.patch)

## Local CPU measurements

Each timing covers 4 MiB in 16 KiB pieces. Entries are medians of 17 alternating pairs in the optimized Windows build on a Ryzen 7 3700X. Copying the initial data back into the two writable buffers happened outside the timer. The test samples repeatable change patterns and one warm cache regime. The table measures just the merge function.

| GPU changes in the input | Original (µs) | AVX2 (µs) |
| --- | ---: | ---: |
| No bytes changed | 505 | 290 |
| Every byte | 629 | 585 |
| Every fourth byte | 609 | 567 |
| Every 16th byte | 476 | 446 |
| Every 64th byte | 454 | 437 |
| Every 512th byte | 468 | 306 |
| Every 4096th byte | 502 | 310 |

## Reproduce

Apply the [paired-wave renderer patch](../../patches/victory-rtx3090-paired-waves.patch) to base `1ffff57a192c8a225118ae946ab21635c38442be` first. The AVX2 patch applies both there and after the upstream 16 KiB transfer change. Commands below assume that PowerShell is in the renderer checkout and the bringup report repository is its sibling.

```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/victory-relay-merge-avx2.patch).Path
git apply --check $patch
git apply $patch
$env:VICTORY_MERGE_AVX2 = '1'
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib avx2_merge_preserves
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib relay_tests -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib time_relay_merge_for_sparse_and_dense_changes -- --ignored --nocapture
```

The differential test checks unaligned buffers, tails, CPU-only writes, stale references and unchanged output. It and all eight existing relay tests passed on the test PC. The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for this local patch and measurements. The underlying relay and its reference merge come from VIctory.
