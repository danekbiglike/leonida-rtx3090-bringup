# RTX 3090 buffer refresh and long frames

## A 3.38-second gameplay frame

The heaviest frame in the additional prison route took 3,380.487 ms for 5,571 draws. Its interval ran from 1,592.361715 to 1,595.742202 seconds in the successful-Present trace. The final Present maps to 01:40:45.583333 UTC. The renderer printed its two-frame interval 0.435 ms later. [Route frame times](paired-wave-mips-route-frames.csv) · [Route summary](paired-wave-mips-route-summary.json)

| Renderer measurement | Mean per frame over those two frames |
| --- | ---: |
| Frame time | 1,831.0 ms |
| Preparing submissions | 1,673.7 ms |
| Buffer copies and refresh preparation | 1,641.2 ms, 199.1 MB |
| Texture preparation | 8.0 ms, 12.2 MB |
| Waiting for the GPU | 135.8 ms |
| Copying back | 89.0 ms |
| No GPU work queued while the submitter was working | 1,638.4 ms |

The GPU had little queued work during this stall. The buffer timer includes range preparation, flushes and copies. A flush nested in a title-buffer copy can contribute to more than one timed span. Copy-back can run concurrently. These counters locate the delay on the submission side. They do not isolate a particular memory transfer or establish a disk or driver fault. The separate texture-upload stalls seen during the opening sequence have a different timing signature.

## Local renderer change

A submission can keep the results of a write-watch query until its title-memory dependencies change. Previously each subsequent flush built a vector of watched buffer references, copied and sorted their page ranges, took the journal mutex and then discarded the work if the query was still current. The patch passes a lazy iterator and checks the journal before touching the references. A fresh query still sorts outside the mutex and rechecks under it before updating the journal. Shaders, texture formats, resolution and page tracking use the same settings. [Rust patch](../../patches/victory-lazy-refresh-journal.patch)

Build from the pinned VIctory checkout with the PowerShell recipe. The changed files reproduced byte for byte in a second checkout. Fourteen tests matching `watch::` passed and one was ignored by the suite. The tested executable was built with the diagnostics profile and has SHA-256 `25C0AAC41D456A5F3A6F7B4D256B59F4D42638017FDFA3F150F1A2C5BEFE1A90`. The project owner credits local code primarily to ChatGPT Astra 6.2 at very high reasoning effort. The underlying renderer and write-watch implementation are VIctory contributors’ work.

```powershell
.\tools\prepare-rtx3090-worktree.ps1 -RendererRepo C:\src\VIctory -Destination C:\src\VIctory-journal -Variant Journal
Set-Location C:\src\VIctory-journal
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib watch:: -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
```

Use the existing [TextureLOD profile](../../profiles/rtx3090-paired-texture-lod.ps1) with this build.

## Comparing full uploads with changed 256-byte blocks

This experiment ran on the unchanged TextureLOD executable. At the prison window with the movement prompt visible, the renderer alternated its existing `VICTORY_COPY_CHANGED=alt` modes every 20 seconds. The sample was fixed in advance at 680–840 seconds from the first Present. Frames crossing a mode switch or the one-second margin on either side are reported separately. A second clock anchor differed by 0.6 ms. No movement inputs were sent during the sample.

| Measurement | Whole ranges | Changed 256-byte blocks |
| --- | ---: | ---: |
| Accepted frames | 308 | 307 |
| Average FPS | 4.329 | 4.325 |
| P95 / maximum frame, ms | 277.1 / 300.3 | 267.7 / 306.9 |
| Frames over 200 ms | 278 | 290 |
| Average draws per frame | 4,876 | 4,886 |
| Data uploaded per frame, MB | 116.9 | 22.5 |
| Upload ranges per frame | 709 | 4,706 |
| CPU buffer copy / refresh time, ms | 50.5 | 59.1 |
| GPU wait, ms | 108.8 | 97.1 |

The last four rows are medians of eight complete renderer reporting intervals per mode. Sending only changed blocks reduced upload traffic by 81% and multiplied the number of ranges by 6.6. The CPU spent more time preparing them. The net FPS difference was under 0.1%. The default profile keeps whole-range uploads. Zero- and two-second margins yield the same ordering. [Summaries including boundary frames](copy-refresh/summary.json) · [Renderer interval data](copy-refresh/stages.csv)

Reproduce the comparison from the public trace with Python 3.11 or later in the repository root.

```powershell
$sample = 'reports/2026-11-26-rtx3090/copy-refresh'
python tools/compare_refresh_modes.py "$sample/present.csv" "$sample/switches.log.txt" "$sample/anchor.json" --start 680 --seconds 160 --guard 1
```
