# Parallel GPU copy-back on the RTX 3090

Tested on Windows with a Ryzen 7 3700X and RTX 3090. Starting from the [descriptor refresh build](descriptor-refresh.md), this trial adapts UwUCammie’s parallel GPU copy-back to the paired-wave renderer. The patch groups clipped pieces by their absolute 64 KiB game-memory page. Overlapping CPU spans retain their original order. This preserves the newer branch’s locking and the existing local AVX2 merge. [Upstream PR 1066](https://github.com/fxceless/victory-fork/pull/1066) · [Exact patch](../../patches/victory-parallel-relay-rtx3090.patch)

## Reproduction

Apply the descriptor refresh report's patches and profile first. From the renderer checkout, run the commands below in PowerShell. Ten relay tests and one additional card-merge test passed. The ignored test is a CPU microbenchmark. The tested executable has SHA-256 `B1895ACF4DCDB69C081E4366C147EF4D3F78D892536B5DF01A658158127FE594`.

```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/victory-parallel-relay-rtx3090.patch).Path
git apply --check $patch
git apply $patch
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib relay -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib card_merge -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
. ../leonida-rtx3090-bringup/profiles/rtx3090-paired-avx2.ps1
$env:VICTORY_WIDE_MERGE = '1'
```

The project owner credits local code, integration and benchmark work primarily to ChatGPT Astra 6.2 at very high reasoning effort. UwUCammie authored the upstream parallelization.


## Prepare the exact renderer sources

With the upstream renderer and this report repository in sibling directories, run the following in PowerShell. The preparation script creates a new worktree at the measured base revision and applies the patches in order, including the keyboard-axis handling used during gameplay. The AVX2, Descriptors and Parallel variants reproduced each corresponding measured source tree, including every changed file. All nine GameInput tests passed in the reconstructed Parallel checkout. The original renderer checkout is left at its current revision. [Preparation script](../../tools/prepare-rtx3090-worktree.ps1) · [Keyboard movement patch](../../patches/victory-keyboard-movement-3090.patch)

```powershell
.\leonida-rtx3090-bringup\tools\prepare-rtx3090-worktree.ps1 -RendererRepo .\victory-fork -Destination .\victory-3090-parallel -Variant Parallel
Set-Location .\victory-3090-parallel
cargo build --locked --profile diag --features diagnostics -p victory
. ..\leonida-rtx3090-bringup\profiles\rtx3090-paired-avx2.ps1
$env:VICTORY_WIDE_MERGE = '1'
```

For the earlier all-round build select `-Variant AVX2` and use its matching profile. For the descriptor refresh trial select `-Variant Descriptors` and use the same AVX2 profile. A launcher which creates a fresh environment needs to forward the profile variables to the renderer.

On this CPU the 90-second window sample reached 4.34 FPS compared with 4.61 on the descriptor build. Mean draw counts were 4,861 and 4,850. Median diagnostic time spent copying results back rose from 91.0 to 106.3 ms. Facing the door the two builds measured 3.36 and 3.43 FPS respectively. These measurements do not reproduce the improvement that the upstream author reported on an RX 7900 XT. Smaller rectangular highlights remain visible in the hair in the door view. [Descriptor trial](descriptor-refresh.md) · [Upstream measurements](https://github.com/fxceless/victory-fork/pull/1066)

## Gameplay on the RTX 3090 and Ryzen 7 3700X

Series X profile, 3840 × 2160 render surfaces. Frame times cover successful DXGI presents. The samples begin at preselected time boundaries after player control. Each camera angle was tested once per build.

| Prison scene | FPS | P95 frame | Slowest frame | Frames within 200 ms | Mean draws | Raw data |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Facing the window, 90 s](paired-wave-land-window.jpg) | 4.34 | 264.7 ms | 298.2 ms | 42 / 391 | 4,861 | [CSV](paired-wave-land-frames.csv) · [JSON](paired-wave-land-summary.json) |
| [Facing the door, 60 s](paired-wave-land-room.jpg) | 3.36 | 351.7 ms | 431.5 ms | 0 / 203 | 6,935 | [CSV](paired-wave-land-room-frames.csv) · [JSON](paired-wave-land-room-summary.json) |
| [With movement keys, 60 s](paired-wave-land-moving.jpg) | 3.36 | 338.3 ms | 379.6 ms | 0 / 203 | 7,456 | [CSV](paired-wave-land-moving-frames.csv) · [JSON](paired-wave-land-moving-summary.json) |

The movement minute includes individual W, A, D and W inputs. Moving the camera changes the number of draws, so compare like scenes across builds. The two stationary samples exercise lighter and heavier views of the same room.

During the movement sample the guard stood in the open doorway. The descriptor trial’s four-input sample ended in the hallway, so the movement FPS values cover different views. For the same guard-and-door scene there is also a [two-input comparison on the descriptor build](paired-wave-heaps-two-keys-summary.json). For this machine the parallel version has no measured advantage at either stationary angle.
