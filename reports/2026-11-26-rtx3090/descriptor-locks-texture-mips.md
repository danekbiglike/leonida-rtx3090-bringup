# Descriptor contention and streamed texture mip levels

This build combines the [joined-readback renderer](join-fetch-ranges.md) with two independently testable patches. The first ports beamdotdev’s descriptor-lock and command-list recycling work. A completed descriptor can be read without serializing every recording thread on one heap mutex. Cached keys are cleared before the slot changes. The tested profile moves completed list recycling to a worker. The port keeps the local buffer-view and batched invalidation paths. [Upstream PR 1146](https://github.com/fxceless/victory-fork/pull/1146) · [Exact port](../../patches/victory-recording-locks-rtx3090.patch)

The second patch is BradRoland’s fix to streamed 2D and 2D-array views. The title’s minimum LOD is in resource coordinates. When the first resident mip changes, subtracting that shift from the minimum could expose the wrong mip. The fix preserves the minimum. The regression passed on both the RTX 3090 and WARP. Twenty descriptor tests and ten relay tests also passed. [Upstream PR 1210](https://github.com/fxceless/victory-fork/pull/1210) · [Exact upstream patch](../../patches/upstream-pr1210-resource-min-lod.patch)

## Reproduction

Prepare the joined renderer, then apply the two patches above. Build the diagnostics profile and use the same options as the joined renderer with one addition, `VICTORY_LAND_ASIDE=1`. The descriptor-cache changes and mip correction are enabled by default in this build. The executable SHA-256 is `C39E44518B0EE2DE745706170D32B315D55569A6F537CE764DDE776902FF0DA2`. Local integration and evaluation are credited by the project owner primarily to ChatGPT Astra 6.2 at very high reasoning effort.

```powershell
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib show_from -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib descriptor::host:: -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
$env:VICTORY_LAND_ASIDE = '1'
```


To reproduce the full checkout, run the [worktree script](../../tools/prepare-rtx3090-worktree.ps1) with `-Variant TextureLOD`. All 13 changed source files matched the renderer used on the test PC after applying the published patches.

The [complete PowerShell profile](../../profiles/rtx3090-paired-texture-lod.ps1) sets the graphics and performance switches used in the native launcher. Dot-source it in the PowerShell session that starts the renderer.

## Outdoor skin and lighting

In the wide shot with the Russian “ДЕНЬГИ ПРЯМО СЕЙЧАС” subtitle, the dark square patches previously visible on the character’s exposed arms and thighs are absent in this capture. The floor and chair are missing, vehicles use coarse geometry, and an earlier shot is almost entirely overexposed. These frames are from the opening cutscene and do not count toward the gameplay benchmark. Multiple renderer changes and differences in streaming state mean these pictures cannot establish that the mip fix alone improved the skin. [Seated character](paired-wave-mips-cutscene-seated.jpg) · [Overexposed shot](paired-wave-mips-cutscene-transition.jpg)

A second frame from the same seated sequence still shows continuous skin across the arms and thighs, with floating rectangles in the sky and distant scenery missing. [Later frame](paired-wave-mips-cutscene-seated-later.jpg)

## Window frame times

The 90-second window sample recorded 421 accepted presents in 90.26 seconds, or 4.66 FPS, up from 4.43 with joined readbacks alone. Average draw counts were 4,612 and 4,629. Median relay landing time fell from 89.6 to 73.7 ms; P95 frame time fell from 250.8 to 245.6 ms. Only 23 of the 421 frames met the 200 ms budget. The largest shoulder halo remains absent and the bands in the hair persist. [Current frame data](paired-wave-mips-summary.json) · [Previous frame data](paired-wave-spans-summary.json)

## Gameplay on the RTX 3090 and Ryzen 7 3700X

Series X profile, 3840 × 2160 render surfaces. Frame times cover successful DXGI presents. The samples begin at preselected time boundaries after player control. Each camera angle was tested once per build.

| Prison scene | FPS | P95 frame | Slowest frame | Frames within 200 ms | Mean draws | Raw data |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Facing the window, 90 s](paired-wave-mips-window.jpg) | 4.66 | 245.6 ms | 277.3 ms | 23 / 421 | 4,612 | [CSV](paired-wave-mips-frames.csv) · [JSON](paired-wave-mips-summary.json) |
| [Facing the door, 60 s](paired-wave-mips-room.jpg) | 3.93 | 300.5 ms | 342.2 ms | 2 / 237 | 6,898 | [CSV](paired-wave-mips-room-frames.csv) · [JSON](paired-wave-mips-room-summary.json) |
| [With movement keys, 60 s](paired-wave-mips-moving.jpg) | 3.91 | 298.4 ms | 391.3 ms | 0 / 235 | 6,894 | [CSV](paired-wave-mips-moving-frames.csv) · [JSON](paired-wave-mips-moving-summary.json) |

The movement minute includes individual W, A, D and W inputs. Moving the camera changes the number of draws, so compare like scenes across builds. The two stationary samples exercise lighter and heavier views of the same room.

Facing the door improved from 3.59 to 3.93 FPS. P95 fell from 329.0 to 300.5 ms while draw counts rose slightly, from 6,846 to 6,898. The four-key minute improved from 3.41 to 3.91 FPS, with P95 down from 336.7 to 298.4 ms; every frame in that minute still exceeded 200 ms. These are single runs for each build, with slightly different animation and input timing. Both fixed-angle views also improved against the earlier AVX2 profile at 4.45 and 3.58 FPS. This is the selected profile on this PC.

## Additional minute with forward input requested

After the three matched samples an additional 60.23 seconds recorded 166 frames, averaging **2.76 FPS**, P95 639.0 ms and a maximum 3,380.5 ms. The movement automation timed out before reporting how many forward inputs were delivered. The successful-present trace and long stalls were captured independently. This case is included in the comparison index. [Per-frame CSV](paired-wave-mips-route-frames.csv) · [Timing summary](paired-wave-mips-route-summary.json)
