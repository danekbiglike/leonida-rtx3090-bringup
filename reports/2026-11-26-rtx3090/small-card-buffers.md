# RTX 3090 gameplay with small buffers in GPU memory

The prison window averaged **5.46 FPS** for 90 seconds on the Ryzen 7 3700X and RTX 3090. Facing the door averaged 4.18 FPS. Moving out of the cell and then following the guard into a busier room averaged 3.73 and 2.90 FPS. The Series X graphics preset, output resolution and paired-wave lighting stayed the same. The small-buffer profile is available alongside the earlier TextureLOD profile. [PowerShell profile](../../profiles/rtx3090-small-card-buffers.ps1) · [Earlier build](descriptor-locks-texture-mips.md)

| Live gameplay | Frames / seconds | Average FPS | P95 / longest frame, ms | Frames within 200 ms | Five-second windows at 5 FPS or higher |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Facing the window](paired-wave-cardsync-summary.json) | 492 / 90.11 | 5.46 | 208 / 262 | 440 / 492 | 18 / 18 |
| [Facing the door](paired-wave-cardsync-room-summary.json) | 251 / 60.03 | 4.18 | 276 / 517 | 11 / 251 | 0 / 12 |
| [Leaving the cell](paired-wave-cardsync-moving-summary.json) | 225 / 60.33 | 3.73 | 487 / 804 | 14 / 225 | 0 / 12 |
| [Following the guard](paired-wave-cardsync-route-summary.json) | 176 / 60.65 | 2.90 | 781 / 2,000 | 0 / 176 | 0 / 12 |

The slowest five seconds at the window still delivered 26 frames. Movement through the crowded room fell to eight frames in five seconds. The earlier build measured 4.66 at the window and 3.93 at the door. Its movement samples covered different routes. Reaching the corridor and the phone area changes the workload enough that an FPS difference between routes cannot establish a speedup. [Counts for every five seconds](small-card-five-second-windows.json) · [Build comparison](gameplay-comparison.md)

## Run on another RTX 3090

Build the pinned renderer with the `Upload4K` recipe. From the report repository in PowerShell, load the profile in the environment passed to the renderer. A wrapper that creates a new environment must forward the profile variables. The local run used whole-range uploads. The small buffers used the upstream 64 KiB threshold and 1,280 MiB setting. This changes where the renderer keeps copies of buffers that shaders access. It preserves the scene's shading and texture settings. The tested executable had SHA-256 `40D05895E7E67A6D567F96D648B42EC92C6440CCF8189EA1764D7651E997C6CF`. [Build recipe, source and tests](upload-chunks-and-textures.md#reproduce-the-build) · [Upstream measurements and setting descriptions](https://github.com/fxceless/victory-fork)

```powershell
. .\profiles\rtx3090-small-card-buffers.ps1 -FrameCsv "$PWD\frame-times.csv"
```

The data count successful DXGI presents. The FPS calculation includes whole intervals crossing either endpoint. The five-second counts assign each present to the window in which it ended. Both input routes have eight physical keypresses bracketed by readings of the same present clock. We excluded an earlier planned movement interval because the keys arrived after it. The renderer's native frame capture finished before both input routes. Screenshots show the room before the capture, the corridor after the first route and the common room after the second. [Window](paired-wave-cardsync-window.jpg) · [Door](paired-wave-cardsync-room.jpg) · [Corridor](paired-wave-cardsync-hall.jpg) · [Common room](paired-wave-cardsync-common-room.jpg) · [First input trace](small-card-inputs.json) · [Second input trace](small-card-corridor-inputs.json)

Reproduce the published window measurement with Python 3. The same commands accept the other frame CSVs with the starts given in their JSON summaries.

```powershell
$frames = 'reports/2026-11-26-rtx3090/paired-wave-cardsync-frames.csv'
python tools/summarize_gameplay.py $frames --start 680 --seconds 90
python tools/gameplay_windows.py $frames --start 680 --seconds 90 --window 5
```

## What still costs frame time

Median renderer diagnostic intervals at the window reported 55 ms waiting on the GPU and 69 ms preparing buffer copies per frame. Facing the door reported 99 and 62 ms respectively. On the second route the medians were 88 and 93 ms. These stages can overlap. During the interval ending alongside the 1.51 s hitch, texture refreshes across threads averaged 617 ms per frame, including 510 ms waiting for the game memory mapping to become stable. This identifies a wait to investigate during streaming. The timing cannot account for every hitch on the route. [Stage counters](small-card-stages.csv) · [Texture counters around the hitches](small-card-texture-waits.csv)

## Rectangular lighting bands

The outer edge of Lucia's sunlit shoulder at the window looks continuous in this run. Horizontal rectangles remain across her hair in the door view. VIctory saved 455 intermediate pictures across 24 frames during a single diagnostic request. The striped head is visible in the RGBA8 intermediate and in late color. The crops come from different frames and do not identify which pass first introduced the pattern. The four compute shader hashes highlighted in the older RTX 4080 issue had zero exact matches in the event listing from the first captured frame. Other frames and shaders remain open. [Game window showing the hair](paired-wave-cardsync-moving.jpg) · [Three intermediate crops](small-card-hair-detail.jpg) · [RTX 4080 upstream issue](https://github.com/fxceless/victory-fork/issues/62)

The upstream VIctory contributors implemented the GPU buffer placement and the batched synchronization path. The project owner credits the local code primarily to ChatGPT Astra 6.2 at very high reasoning effort. This repository adds the RTX 3090 profile, local renderer patches, raw frame intervals, analysis and reproduction commands. [Renderer contributors and patch origins](upload-chunks-and-textures.md) · [License](../../LICENSE)
