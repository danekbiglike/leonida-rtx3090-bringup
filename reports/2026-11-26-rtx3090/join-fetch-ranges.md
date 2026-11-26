# Joining adjacent GPU readbacks on the RTX 3090

The RTX 3090 trace shows thousands of 16 KiB pieces fetched every frame. This local patch records adjacent pieces as a single Direct3D 12 copy when they belong to the same buffer and their source and destination offsets are both contiguous. The CPU still checks and merges every piece in its original order. It applies to both the direct queue and the separate readback queue. The switch defaults off. [Exact renderer patch](../../patches/victory-join-fetch-ranges-rtx3090.patch)

## Verification and reproduction

Apply the [parallel relay patch set](parallel-relay.md) and then this patch. The differential unit test compares every expanded source and destination byte against the original command sequence, including a missing source range, a destination gap, two separate resources of the same value and an empty list. That test and ten relay tests passed. The test executable has SHA-256 `85EF756FF3FB623FA31028A6B68F6361D5681931110697A8F4D7FAF9E55F48A1`.

```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/victory-join-fetch-ranges-rtx3090.patch).Path
git apply --check $patch
git apply $patch
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib fetch_range_tests
cargo build --locked --profile diag --features diagnostics -p victory
$env:VICTORY_JOIN_FETCH_RANGES = '1'
```

The diagnostic line `relay readback per frame` reports source pieces and D3D12 commands separately. The project owner credits this local patch primarily to ChatGPT Astra 6.2 at very high reasoning effort. The underlying readback and queue code belongs to its upstream authors.


For the complete renderer source use the [preparation script](../../tools/prepare-rtx3090-worktree.ps1) with `-Variant Joined`. In a fresh checkout this reproduced every changed source file from the local build. To enable the measured code path, use the AVX2 profile from the parallel relay report, set `VICTORY_WIDE_MERGE=1` and `VICTORY_JOIN_FETCH_RANGES=1`, and forward both variables to the renderer.

## Readback commands in gameplay

At the prison window the median was 4,660 pieces per frame and 725 Direct3D 12 copy commands. Across the 80 diagnostic intervals the median command-count reduction was 84.48%. The 90-second accepted-present average was 4.43 FPS; the previous build measured 4.34. The new run drew 4,629 calls per frame against 4,861, so the small FPS difference is inconclusive. Median time inside relay landing fell from 108.0 to 89.6 ms. P95 frame time went from 264.7 to 250.8 ms. [New measurement](paired-wave-spans-summary.json) · [Baseline](paired-wave-land-summary.json)

## Gameplay on the RTX 3090 and Ryzen 7 3700X

Series X profile, 3840 × 2160 render surfaces. Frame times cover successful DXGI presents. The samples begin at preselected time boundaries after player control. Each camera angle was tested once per build.

| Prison scene | FPS | P95 frame | Slowest frame | Frames within 200 ms | Mean draws | Raw data |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Facing the window, 90 s](paired-wave-spans-window.jpg) | 4.43 | 250.8 ms | 282.6 ms | 30 / 400 | 4,629 | [CSV](paired-wave-spans-frames.csv) · [JSON](paired-wave-spans-summary.json) |
| [Facing the door, 60 s](paired-wave-spans-room.jpg) | 3.59 | 329.0 ms | 344.5 ms | 0 / 216 | 6,846 | [CSV](paired-wave-spans-room-frames.csv) · [JSON](paired-wave-spans-room-summary.json) |
| [With movement keys, 60 s](paired-wave-spans-moving.jpg) | 3.41 | 336.7 ms | 610.1 ms | 0 / 205 | 6,976 | [CSV](paired-wave-spans-moving-frames.csv) · [JSON](paired-wave-spans-moving-summary.json) |

The movement minute includes individual W, A, D and W inputs. Moving the camera changes the number of draws, so compare like scenes across builds. The two stationary samples exercise lighter and heavier views of the same room.

Facing the door, median command-count reduction reached 87.49%. The run averaged 3.59 FPS, up from 3.36, with 6,846 rather than 6,935 draws per frame. In the keyboard-input minute we measured an 88.41% command-count reduction and 3.41 FPS. The closed door and character positions in the screenshot differ from the previous movement run. Each of these two samples exceeded 200 ms on every frame. The large shoulder rim stayed clear, with rectangular bands still visible in the hair.
