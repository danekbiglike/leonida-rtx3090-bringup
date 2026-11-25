# GTA VI gameplay on Windows with VIctory and RTX 3090

The prison scene measured **3.39 FPS before and 3.42 FPS after** a local texture-streaming optimization. The difference in that scene was within run-to-run variation. Both texture-test modes showed square lighting artifacts. A subsequent paired-wave build removed the stepped outline at the prison window and measured 2.58 FPS in player control, rising to 3.16 FPS with the separate copy queue. The next memory profile reached 3.96 FPS at the window and 2.98 FPS looking into the room. Stable 5 FPS remains an open target. [Memory profile and raw data](paired-wave-pieces.md) [Prison-window lighting tests, per-frame CSV and reproduction](lighting-trial.md) [Paired-wave RTX 3090 gameplay comparison](paired-waves.md)

| Workload | Original | Patched | Comparison |
| --- | ---: | ---: | --- |
| Changing 3D scenes in the prologue | 2.54 FPS | 3.33 FPS | 45 matched pairs, camera and streaming load varied |
| Prison window, about 5,000 draws per frame | 3.39 FPS | 3.42 FPS | 18 intervals per mode |
| Querying 4 MiB of resident texture data | 26.2 µs | 3.0 µs | Local CPU benchmark, 64 equally spaced page probes |

Ryzen 7 3700X, GeForce RTX 3090, Windows, Series X profile. Both modes used the same process, graphics settings, saved state and shader cache. FPS is total frames divided by total time. The primary sample spans four minutes after the first interval with at least 800 draws per frame. Blocks of four approximately one-second intervals followed an ABBA schedule. The comparison discarded the first interval of each block and paired nearby intervals within 10% of each other by draw count. Across those pairs the median frame-time change was −2.9%. Averages over these intervals cannot establish an individual-frame percentile. [Measurements and selection rules](measurements.json)

## Apply the patch

The patch applies to revision `9376fd60c0ba0e76a74c39b49b1407dbac0a64c7` of fxceless/victory-fork. It batches Windows working-set queries and caches the allocation size for each complete texture descriptor. The renderer still probes nonresident samples for readability. The per-thread size cache holds at most 1,024 descriptions. [Patch](../../patches/victory-texture-residency-rtx3090.patch) · [Upstream revision](https://github.com/fxceless/victory-fork/commit/9376fd60c0ba0e76a74c39b49b1407dbac0a64c7)

From this report repository's root, on Windows with Git and the upstream Rust/MSVC build prerequisites installed, run the following in PowerShell.

```powershell
$patch = (Resolve-Path patches/victory-texture-residency-rtx3090.patch).Path
git clone https://github.com/fxceless/victory-fork.git victory-streaming-test
Set-Location victory-streaming-test
git checkout --detach 9376fd60c0ba0e76a74c39b49b1407dbac0a64c7
git apply --check $patch
git apply $patch
cargo test --locked --profile diag -p victory-gpu --features diagnostics --lib texture::title_memory_tests -- --test-threads=1
cargo test --locked --profile diag -p victory-gpu --features diagnostics --lib cached_sizes_match_layouts_across_eviction
cargo build --locked --profile diag -p victory --features diagnostics
```

Use `target/diag/victory.exe` in your existing launcher. The ordinary run enables both optimizations. For comparison, pass `VICTORY_RESIDENCY_AB=1` to the **renderer process**. A launcher that constructs a fresh environment must explicitly forward it. Each `texture residency comparison` log line includes the mode, frame count, mean frame time, draw count and probe totals. Unset the variable for subsequent ordinary runs.

## Reuse and attribution

VIctory and fxceless/victory-fork provide the emulator. This repository contributes the local patch and RTX 3090 measurements. The project owner credits **ChatGPT Astra 6.2 at very high reasoning effort** as the primary author of this local patch. Credit the upstream authors and link the revision and patch when reporting a derivative. The repository includes the GPLv3 license. [License](../../LICENSE)
