# Descriptor heap lifetime and texture queue on an RTX 3090

Walking down the prison corridor averaged **3.08 FPS**. Entering the common room averaged **2.44 FPS**. None of the 36 five-second windows across the three moving samples delivered 25 frames. The old small-buffer profile averaged 2.90 FPS entering the common room in an earlier launch. The evidence supports keeping its graphics profile available. [Earlier small-buffer measurements](small-card-buffers.md)

| Sixty-second segment | Frames | Average FPS | P95 / longest frame | Slowest five seconds |
| --- | ---: | ---: | ---: | ---: |
| From the cell to the corridor | 160 | 2.65 | 583 / 935 ms | 1.8 FPS |
| Along the corridor with the guard | 186 | 3.08 | 425 / 529 ms | 2.8 FPS |
| Through the gate into the common room | 147 | 2.44 | 639 / 1,245 ms | 1.6 FPS |

Each interval was chosen in advance and includes keyboard movement. The corresponding no-wait experiment measured 1.95, 3.18 and 2.44 FPS. Scene and input timing differ between runs. The improvement on the first transition did not carry through the escort. The corridor diagnostic intervals reported median GPU waits of 119 ms per frame and 93 ms preparing buffer copies. Entering the common room those values were 139 and 88 ms. The timers can overlap. [Present intervals](heap-owner/frame-times.csv) · [Five-second bins and percentiles](heap-owner/segments.json) · [Input times](heap-owner/inputs.json) · [Renderer counters](heap-owner/stages.csv) · [Cell exit](heap-owner/owner-exit-after.jpg) · [Corridor](heap-owner/owner-corridor-after.jpg) · [Common room](heap-owner/owner-common-room-after.jpg)

The launcher set a 42 GiB process cap. The peak through the first 20 minutes was 30.20 GiB, with no memory-limit message in the capture. The logger recorded no destruction of a descriptor heap holding cached views during this interval. The lifetime regression establishes that such views can be released when a heap disappears. Total memory savings on this route remain unverified. The settings file matched the earlier run byte for byte. Shadows and faces in the common room still look dark. [Memory samples](heap-owner/memory.csv) · [Peak and headroom](heap-owner/memory-summary.json) · [Limit messages](heap-owner/memory-events.csv) · [Earlier run that crossed 34 GiB](stream-memory-walk.md)

The previous renderer kept a process-wide table of buffer views, keyed by the address of their descriptor heap. If a heap disappeared with live entries, the table could keep its buffer references until process exit or a later pass at the reused address. This build puts the ranges and pass count in the heap that owns them. An in-flight command list can still keep an underlying resource alive. The change addresses one retention path. Measuring the effect on total memory requires following the game through comparable scenes. [Upstream lifetime fix](https://github.com/fxceless/victory-fork/pull/67) · [Windows memory measurements from the previous launch](stream-memory-walk.md)

The same build counts the texture backlog while selecting the next upload batch. For a capped batch it orders just the entries needed to reproduce the previous schedule: retries first, then alternating newest and oldest fresh entries. The texture data, resolution and upload limits use the stable small-buffer profile. This port keeps the existing descriptor invalidation and locking paths for this renderer revision. [Upstream texture selection change](https://github.com/fxceless/victory-fork/pull/221) · [Exact combined source patch](../../patches/victory-heap-lifetime-texture-queue.patch)

## Reproduce the build

Start from the [tested Upload4K renderer source](upload-chunks-and-textures.md#reproduce-the-build). The patch applies directly to that source and reverse-applies to the tested tree. Use the stable small-buffer PowerShell profile from a fresh shell. The benchmark launcher sets its memory cap separately. The game settings file and output resolution have the same values as the previous escort report. [Graphics profile](../../profiles/rtx3090-small-card-buffers.ps1)

```powershell
git apply "$reportRepo/patches/victory-heap-lifetime-texture-queue.patch"
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib descriptor:: -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
. "$reportRepo/profiles/rtx3090-small-card-buffers.ps1" -FrameCsv "$PWD/frame-times.csv"
```

Thirty descriptor tests passed on Windows, including a test that drops the last retained buffer reference and repeats a first pass at the same heap address. Another test checks upload priority, write tokens and counts for every cap in a mixed queue. The build used for the gameplay run had SHA-256 `6DEDB7745B5ED4F72C63FDAC259BB4A125AA95D3148EEA88FEFAFD26924F5B4B`. The local project owner credits the local integration primarily to ChatGPT Astra 6.2 at very high reasoning effort. The two upstream authors retain credit for their respective changes.
