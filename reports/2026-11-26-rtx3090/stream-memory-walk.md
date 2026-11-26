# Memory pressure and the prison escort on an RTX 3090

The renderer passed the old 34 GiB process limit 29 minutes 42 seconds into this launch. Windows still had 7.63 GiB of system commit headroom at that sample. At the same memory demand, the old launcher would have refused more committed memory. The earlier session ended after a 4 MiB allocation failed. It had no process commit trace, so its exact condition at the failed allocation remains unknown. Three seconds before that failure the GPU used 13,382 MiB of a 23,557 MiB local budget. [Previous session](short-buffer-hashes.md) · [Job peak and system memory](stream-memory/memory-summary.json) · [Windows process limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)

## Walking measurements

The Series X settings file matched the stable small-buffer profile byte for byte (SHA-256 `558C63CA0073281E52487C52238BE017CED26837D62E49F896F00ACF537A4D22`, configured fullscreen output 3840 × 2160). The single renderer change relative to the small-buffer profile was `VICTORY_TEXTURE_NO_WAIT=1`. The executable matched that profile (SHA-256 `40D05895E7E67A6D567F96D648B42EC92C6440CCF8189EA1764D7651E997C6CF`). A separate save directory started from a copy of the previous profile. [PowerShell profile](../../profiles/rtx3090-streaming-no-wait.ps1) · [Baseline and build recipe](small-card-buffers.md)

| Segment, 60 seconds each | Average FPS | P95 frame | Longest frame | Slowest five seconds | Five-second windows reaching 5 FPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Guard at the cell door | 3.69 | 330 ms | 402 ms | 3.4 FPS | 0/12 |
| Leaving the cell | 1.95 | 1,140 ms | 2,245 ms | 1.0 FPS | 0/12 |
| Along the corridor | 3.18 | 377 ms | 451 ms | 3.0 FPS | 0/12 |
| Entering the common room | 2.44 | 599 ms | 1,039 ms | 1.6 FPS | 0/12 |

The last three segments had keyboard input throughout the walk. Each time window was chosen before its first input. The accepted Present clock brackets the keypresses. FPS includes whole frame intervals crossing either endpoint. Five-second counts use the completion time of each interval. The earlier profile measured 2.90 FPS entering the common room in a separate launch. Both routes reached the same area, with different camera positions and streaming history. [Frame intervals](stream-memory/frame-times.csv) · [Window counts and frame percentiles](stream-memory/segments.json) · [Input receipts](stream-memory/inputs.json) · [Cell exit](stream-memory/follow-to-hall-after.jpg) · [Corridor](stream-memory/guard-corridor-after.jpg) · [Common room](stream-memory/guard-common-room-after.jpg)

The median diagnostic interval along the corridor reported 130 ms per frame waiting for GPU work and 96 ms preparing buffer copies. The intervals at the common room reported 163 ms and 86 ms respectively. These timers can overlap. The reported wait for the game to finish remapping texture memory was zero. The renderer instead retries reads of missing pages. At the cell exit, the median interval that reported this path deferred 38.4 refreshes per frame. Along the corridor it deferred 4.6. A delayed refresh can show older texture data until the next attempt. The samples do not establish visual equivalence during streaming. [Renderer times](stream-memory/stages.csv) · [Texture waits](stream-memory/texture.csv) · [Deferred refreshes](stream-memory/retries.csv)

The PC has 32 GiB of RAM. During the corridor sample median available physical memory was 1.02 GiB and the process held 28.43 GiB of private committed memory. The physical disk holding the pagefile recorded a median 161 reads/s with a 27 ms read latency, versus 15 reads/s on the disk holding the game files. These are device-wide counters. They include other activity. File-backed reads also contribute to the Windows page read counter. [Memory samples](stream-memory/memory.csv) · [Device samples](stream-memory/disk.csv) · [GPU memory](stream-memory/vram.csv) · [Sampling clocks](stream-memory/clock.json)

A later test alternated all sixteen logical processors and one logical processor per physical core in four 24-second blocks. In twelve-second intervals inside those blocks the frame rate was 3.10, 1.30, 3.02 and 2.92 FPS. The scene transitioned into a cutscene and draw counts changed. The trial showed no consistent improvement. All processors were restored. The escort table excludes this transition. [Switch times and per-block data](stream-memory/affinity.json)

## Capture the next memory failure

The experimental launcher sampled the child's private memory and the Windows job's peak process commitment every second. It used the former 34 GiB cap as a floor, with up to 42 GiB when startup commit headroom allowed another 6 GiB for the rest of the system. The actual cap was 41.87 GiB. Across the run the peak was 34.25 GiB. VIctory was still responding at 42 minutes 36 seconds and exited normally after a requested close. [Final process samples](stream-memory/closing-samples.csv) Physical memory available to Windows briefly fell to 0.10 GiB. The cap limits an individual process and does not allocate extra RAM. [Windows system memory counters](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information)

The updated stable launcher also registers a completion port on its own empty job before assigning the child. It records Windows process and job memory-limit messages through process exit. A small fixture forced an allocation denial in a separate process with a 32 MiB cap and recorded event 9. An observed message identifies the limit Windows enforced. Delivery of hard-limit messages is best effort. The live no-wait run collected periodic counters only. [Notification receiver](../../tools/job_memory_events.hpp) · [Synthetic test](../../tools/test_job_memory_events.cpp) · [Windows job messages](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port)

From the report checkout, reproduce the corridor and the previous-limit crossing with Python 3. Run the last two commands in an x64 Visual Studio developer shell.

```powershell
$d = 'reports/2026-11-26-rtx3090/stream-memory'
python tools/summarize_gameplay.py "$d/frame-times.csv" --start 1133 --seconds 60
python tools/gameplay_windows.py "$d/frame-times.csv" --start 1133 --seconds 60
python tools/summarize_memory_capture.py "$d/memory.csv" --old-cap-gib 34
cl /nologo /std:c++17 /EHsc tools/test_job_memory_events.cpp
.\test_job_memory_events.exe
```
