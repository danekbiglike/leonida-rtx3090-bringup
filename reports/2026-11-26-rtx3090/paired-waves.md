# Paired-wave rendering on RTX 3090

**2.58 FPS at the prison window.** A preselected 90-second sample on the Ryzen 7 3700X and RTX 3090 recorded 233 accepted presents. The median interval was 383.4 ms, P95 was 431.0 ms and the longest was 1212.8 ms. 233 of 233 intervals exceeded 200 ms, at a mean of 4884 draws per frame. [Full per-frame CSV](paired-wave-frames.csv) · [Machine-readable summary](paired-wave-summary.json)

This run targets the stair-stepped sunlight on Lucia’s hair and shoulder at the prison window. On an RTX 4090 a tester could switch the defect off and back on across runs using paired waves on the PR 994 stack, with the acceleration-structure builder enabled. The prior local depth build still dropped the tester’s `f133e35efed2a48a` compute shader. [Independent comparison](https://github.com/fxceless/victory-fork/issues/62#issuecomment-7175666292) · [Previous RTX 3090 measurement](window-depth.md)

## Reproduction

The base is the full PR 994 tree at `1ffff57a192c8a225118ae946ab21635c38442be`, including the shader and dispatch changes from PRs 854 and 993. In the paired form, one 32-lane host wave represents one 64-lane console wave. PR 994 adds support for the game's acceleration-structure builder. PR 1014 distributes comparison of each 64 KiB buffer piece across a workgroup. That change targets GPU work in copying changed data back to the emulated game. [PR 854](https://github.com/fxceless/victory-fork/pull/854) · [PR 993](https://github.com/fxceless/victory-fork/pull/993) · [PR 994](https://github.com/fxceless/victory-fork/pull/994) · [PR 1014](https://github.com/fxceless/victory-fork/pull/1014)

The [standalone renderer patch](../../patches/victory-rtx3090-paired-waves.patch) includes PR 1014 ported to this revision, our previous texture and write-range optimizations, accepted-present logging and the switch for diagnostic frame readbacks. Apply it directly to the revision above. Local input and profile integration depend on the launcher and are outside the graphics patch.

```powershell
$patch = (Resolve-Path patches/victory-rtx3090-paired-waves.patch).Path
git clone https://github.com/fxceless/victory-fork.git victory-waves
Set-Location victory-waves
git fetch origin refs/pull/994/head
git checkout --detach 1ffff57a192c8a225118ae946ab21635c38442be
git apply --check $patch
git apply $patch
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib warp_card_compare_finds_every_byte_with_skew
cargo test --locked --profile diag --features diagnostics -p victory-shader --lib a_wave_value_used_past_a_lane_branch_takes_the_paired_form_not_an_approximate_one
cargo build --locked --profile diag --features diagnostics -p victory
```

Both focused tests passed on the test PC. Give this build its own writable cache and save copy. The same Series X graphics profile was used across runs. The renderer environment for this trial follows.

```powershell
$env:VICTORY_WAVE_PAIRS = '1'
$env:VICTORY_BVH_BUILDER = '1'
$env:VICTORY_CARD_REHASH_RUNS = '1'
$env:VICTORY_BLACK_FRAME_PROBE = '0'
$env:VICTORY_MEMORY_MAP = '0'
$env:VICTORY_LOG = 'warn,victory_gpu::host=info'
$env:VICTORY_FRAME_CSV = Join-Path $PWD 'paired-wave-frames.csv'
```

Use a fresh CSV path when repeating the run. The native counter records the interval between accepted DXGI presents and the draw count. A launcher that constructs its own environment must forward these variables. The upstream wave, builder and comparison-shader authors are credited above. The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for the local changes, integration and RTX 3090 measurements.

## What changed on screen

At the same prison window, the sunlit shoulder and hair lost the large rectangular steps seen in the previous build. After turning Lucia into the room with the movement key, the lit hair retained individual strands. The window looks more diffuse, and the floor still has conspicuous patches. This is a visual comparison of two angles in one playable room. The other skin and lighting artifacts in outdoor scenes have not been retested. [Previous window](window-depth.jpg) · [Paired waves at the window](paired-wave-window.jpg) · [After turning into the room](paired-wave-room.jpg)

Across 16 diagnostic intervals the median reported copy-back time was 193.3 ms, texture preparation was 7.3 ms, and the median number of draws discarded for lack of a host pipeline was zero (365 in the depth run). These timings overlap. FPS fell from 2.97 to 2.58 in this scene. Both trials used the same graphics settings. The change of upstream revision and enabled features prevents attributing the visual change to any single switch.

На RTX 3090 крупные световые ступени на плече у окна исчезли. При повороте в камеру волосы тоже освещены ровнее. В этой сцене осталось 2,58 FPS, на полу заметны другие артефакты.

## In-flight readback on the same binary

Turning on `VICTORY_CARD_FETCH_INFLIGHT=1` with `VICTORY_CARD_FETCH_INFLIGHT_MB=128` slowed the fixed-window run to **2.19 FPS**. The large shoulder blocks remained absent. Keyboard movement after the timed sample turned Lucia away from the window. Use the paired-wave configuration above for the 2.58 FPS result. [Window screenshot](paired-wave-fetch-window.jpg) · [Per-frame CSV](paired-wave-fetch-frames.csv) · [Summary](paired-wave-fetch-summary.json)

| Mode | Accepted frames | FPS | P95 interval | Over 200 ms | Mean draws |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original transfers | 233 | 2.58 | 431.0 ms | 233 | 4,884 |
| Fetch inside the flight, 128 MiB | 198 | 2.19 | 591.9 ms | 198 | 4,888 |

The second measurement covers elapsed seconds 1050–1140 in the per-frame capture. The game save was copied from the same starting profile. The executable, paired shaders, graphics settings and camera were the same, and this launch reused the pipeline cache. Median time waiting specifically for a fetch fell from 50.3 ms to zero, but the landing thread spent 227.1 ms waiting for other GPU work compared with 76.1 ms before. The fine-grained relay counters sampled 72 intervals during the in-flight run. They showed 101.5 MB per frame fetched inside the flight and zero median fallback landings. Texture preparation was 6.7 ms. The separate GPU frame diagnostic sampled 15 intervals. These counters overlap.

## Separate copy queue and batched draw submission

On the same binary, the queue profile raised the fixed-window sample from **2.58 to 3.16 FPS**. P95 fell from 431.0 to 356.9 ms. The 285 accepted presents spanned 90.29 seconds; every interval exceeded 200 ms. Mean draws were 4,732 versus 4,884 previously. The median reported buffer preparation time for copies fell from 97.8 to 47.1 ms. This comparison covers eight switches as a group, with separate launches. A short helper compilation overlapped the opening seconds of the queue sample. [Window screenshot](paired-wave-queue-window.jpg) · [Per-frame CSV](paired-wave-queue-frames.csv) · [Summary](paired-wave-queue-summary.json)

The previous large rectangular rim did not appear at the window or after turning toward the door. The latter view rendered the fluorescent lights, wall, door and floor. Dark patches remain on parts of the partition and floor. [Room after turning](paired-wave-queue-room.jpg)

From a fresh PowerShell session, dot-source the [RTX 3090 queue profile](../../profiles/rtx3090-paired-queue.ps1) before starting the patched emulator. Use a fresh path when collecting frames. Custom launchers must forward the profile settings into the renderer process.

```powershell
. .\profiles\rtx3090-paired-queue.ps1 -FrameCsv .\queue-gameplay.csv
```

Eight options changed relative to the 2.58 FPS run: ASYNC_SUBMIT=1, QUEUE2=1, INDIRECT_WINDOW=1, INDIRECT_GATHER=1, COPY_PLAIN=1, JOIN_PARTS=1, BACK_OWN_VIEW=1 and STAGING_POOL=0 (all with the VICTORY_ prefix). The in-flight fetch experiment was disabled. The console graphics profile, displayed resolution and paired shaders stayed the same. The standalone renderer patch and base revision are in the reproduction section above.

After the 90-second window sample, the S key turned the character toward the room. The 60-second sample in that heavier view averaged **2.59 FPS** (156 frames, P95 437.3 ms, max 513.9 ms, 6,967 draws/frame). All 156 intervals exceeded 200 ms. [Room data](paired-wave-queue-room-frames.csv) · [Room summary](paired-wave-queue-room-summary.json)

During ten warm-up system samples, Windows reported 676–2,020 MiB of available RAM, while the card had approximately 12.5 GiB in use according to nvidia-smi (12,819–12,826 MiB). These samples preceded the timed run. The GPU process diagnostics also reported about 8.5 GB of shared memory on one observation. These readings motivate testing smaller transfers and moving allocations to dedicated GPU memory.

A separate opt-in CPU implementation merges device writes in 32-byte groups. It includes a reproducible differential test and isolated timings on the Ryzen 7 3700X. [Local AVX2 patch, measurements and reproduction](relay-merge-avx2.md)
