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

## Gameplay on the same RTX 3090 PC

The local AVX2 build measured **4.45 FPS** at the prison window, compared with **3.96 FPS** on the [same 16 KiB renderer profile without this change](paired-wave-pieces.md). This is a 12.5% increase between these two 90-second runs. The AVX2 run recorded 401 accepted frames, a median interval of 224.9 ms, P95 of 249.8 ms, and a maximum of 337.8 ms. 31 frames met the 200 ms budget and 370 exceeded it. The mean draw counts were 4,903 and 4,870 respectively. Median diagnostic copy-back time fell from 125.8 to 97.8 ms. Each configuration has one sample in this comparison; both used the same copied checkpoint, matching graphics settings and the same cache directory. [AVX2 window](paired-wave-merge-window.jpg) · [CSV](paired-wave-merge-frames.csv) · [JSON](paired-wave-merge-summary.json)

Use the [combined PowerShell profile](../../profiles/rtx3090-paired-avx2.ps1) after building the paired-wave, 16 KiB and AVX2 patches in that order. It inherits the tested queue and memory settings, and selects the local SIMD merge. The measured binary SHA-256 was `17AE6628FB5F1238E511528738ED69CCF49E5615859922854134255DA306FC8B`. The window sample spans elapsed 680–770 seconds in the CSV.

Turning Lucia to face the door raised the draw count to 6,881 per frame. In that view the AVX2 build delivered **3.58 FPS**, up from **2.98 FPS**. Across 60.09 seconds it recorded 215 frames, P95 313.5 ms and a maximum of 366.2 ms. Every frame exceeded 200 ms. The window, character and lit room retained the paired-wave look, with smaller lighting defects still visible. [After turning](paired-wave-merge-room.jpg) · [Room CSV](paired-wave-merge-room-frames.csv) · [Room JSON](paired-wave-merge-room-summary.json)
