# Descriptor refresh on the RTX 3090

Starting from the [verified AVX2 and 16 KiB build](relay-merge-avx2.md#gameplay-on-the-same-rtx-3090-pc), we integrated UwUCammie’s PR 1043. It avoids requeueing buffer slots while refreshing them, batches changes and reuses a buffer lookup for a newly created view. The local port retains the newer descriptor address writes for paired-wave shaders. The GPU and CPU quality settings remained at the previous values. [Upstream PR](https://github.com/fxceless/victory-fork/pull/1043) · [Exact applied patch](../../patches/victory-descriptor-refresh-rtx3090.patch)

Apply this patch after the three patches for the AVX2 profile, with Git for Windows and Rust/MSVC, in the renderer checkout. Twenty descriptor tests and one draw test passed. The measured binary SHA-256 is `24872E8BE0445C98F4524966B78891E1A4E54B167323471CF319D9F3F1385FA3`.

```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/victory-descriptor-refresh-rtx3090.patch).Path
git apply --check $patch
git apply $patch
$env:VICTORY_D3D12_WARP = '1'
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib descriptor::host:: -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib draw:: -- --test-threads=1
Remove-Item Env:VICTORY_D3D12_WARP
cargo build --locked --profile diag --features diagnostics -p victory
```

Use the same [AVX2 launch profile](../../profiles/rtx3090-paired-avx2.ps1). The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for the local port, integration and measurements.

## Frame measurements

With the same AVX2 profile the descriptor port recorded 4.61 FPS at the window, compared with 4.45 FPS in the prior run. Of 416 accepted frames across 90.30 seconds, 42 met the 200 ms budget. P95 was 242.5 ms (249.8 ms previously), maximum 256.0 ms. Mean draw count was 4,850 (4,903 previously). Median diagnostic time per heap pass fell from 41.8 to 28.7 ms across the two runs. The FPS difference is small and the camera workload varies slightly across launches. [Window](paired-wave-heaps-window.jpg) · [CSV](paired-wave-heaps-frames.csv) · [JSON](paired-wave-heaps-summary.json)

## Gameplay on the RTX 3090 and Ryzen 7 3700X

Series X profile, 3840 × 2160 render surfaces. Frame times cover successful DXGI presents. The samples begin at preselected time boundaries after player control. Each camera angle was tested once per build.

| Prison scene | FPS | P95 frame | Slowest frame | Frames within 200 ms | Mean draws | Raw data |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Facing the window, 90 s](paired-wave-heaps-window.jpg) | 4.61 | 242.5 ms | 256.0 ms | 42 / 416 | 4,850 | [CSV](paired-wave-heaps-frames.csv) · [JSON](paired-wave-heaps-summary.json) |
| [Facing the door, 60 s](paired-wave-heaps-room.jpg) | 3.43 | 331.8 ms | 390.9 ms | 0 / 207 | 7,026 | [CSV](paired-wave-heaps-room-frames.csv) · [JSON](paired-wave-heaps-room-summary.json) |
| [With movement keys, 60 s](paired-wave-heaps-moving.jpg) | 3.22 | 418.7 ms | 912.5 ms | 0 / 195 | 6,666 | [CSV](paired-wave-heaps-moving-frames.csv) · [JSON](paired-wave-heaps-moving-summary.json) |

The movement minute includes individual W, A, D and W inputs. Moving the camera changes the number of draws, so compare like scenes across builds. The two stationary samples exercise lighter and heavier views of the same room.

The earlier movement minute received two inputs (W and A) and averaged 3.34 FPS. All 201 frames exceeded 200 ms. The repeated four-input minute reached the hallway and had two frames longer than 860 ms. The two paths cover different positions and NPC activity. [Two-key CSV](paired-wave-heaps-two-keys-frames.csv) · [Two-key JSON](paired-wave-heaps-two-keys-summary.json)

Compared with the previous build the door view dropped from 3.58 to 3.43 FPS while mean draws rose from 6,881 to 7,026. The descriptor pass itself became faster here (58.1 to 37.4 ms median). This test did not justify replacing the previous all-round profile on its own. The broad shoulder halo is absent in the sampled window view. Rectangular highlights remain visible inside the hair in the door view.
