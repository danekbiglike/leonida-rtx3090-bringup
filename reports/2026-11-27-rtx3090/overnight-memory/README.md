# RTX 3090 private memory over eleven hours

Process-private commit grew by **1.41 GiB** between the second and eleventh hours of the worker-off control. The hourly median rose from 34.22 to 35.63 GiB, while the process working set fell from 4.79 to 4.38 GiB. The process exited with code 0 after the last sample at 11 h 12 min 20 s. The Windows job recorded a lifetime peak of 36.04 GiB against its 41.48 GiB process limit. Its memory-limit event file contained only the header.

| Hour since launch | Median private commit (GiB) | Dedicated GPU use (MiB) | Shared GPU use (MiB) | Renderer buffer copies (MiB) | Depth twins alive | Indexed slots queued |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 34.22 | 13,655 | 11,676.5 | 3,301 | 113 | 6,260 |
| 6 | 34.97 | 13,666 | 11,700 | 3,301 | 113 | 6,159 |
| 11 | 35.63 | 13,693 | 11,760 | 3,302 | 113 | 6,074 |

All table cells use hourly medians. Dedicated and shared GPU use come from DXGI. These GPU and renderer counters changed little relative to private commit and do not identify which allocations grew. The run did not record the address-space breakdown. A separate diagnostic run can capture it with `VICTORY_MEMORY_MAP=1` and the `victory_gpu::copystat=info` log filter in the renderer. The renderer groups allocations by guest heaps, host heaps, shared buffers and other categories. Running this scan separately keeps its overhead out of the timed escort.

The host used a Ryzen 7 3700X, 32 GB of system RAM, an RTX 3090 and the Series X profile. The controlled walk took place during the first hour. Its input replay ended after 120 seconds. There is no synchronized movement or scene record for the late hours, so their memory or frame timings cannot establish how the escort itself changes over time. [Paired escort, executable hash and replay](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/9ac81a703e6a1c072b4a2ca9c5fe80e84fe62265/reports/2026-11-26-rtx3090/texture-worker-escort) · [Ten-hour frame timing report](https://github.com/danekbiglike/leonida-rtx3090-bringup/blob/dcadbab0eeab12c1eda68a13e5af0769a38368a0/reports/2026-11-27-rtx3090/control-session-ten-hours.md)

## Data and reproduction

The [hourly CSV](hourly.csv) covers 40,318 approximately one-second Windows samples in eleven full hours and a final partial hour. The [reducer](reduce.py) bins Windows samples by process uptime and renderer reports by UTC using the file creation time of the sampler (18:17:56.528 UTC, November 26). Each renderer metric is sampled at its own log cadence. The final partial hour includes process shutdown. Run `python reduce.py TRACE_DIRECTORY hourly.csv` against the original control trace to reproduce the file.

| Input | SHA-256 |
| --- | --- |
| memory.csv | `53146a0c794fcb0f079a4c4dd0826c2094c75980e4536683c8e65a2fe3d71f01` |
| runtime.log | `781eaa4d8b44791febabe8d21522654db1ad2701a5a73bdd64203760de69da2e` |
| memory-events.csv | `41276e9e3a3d98ef89ad43bf0a5f83915e6941a37c551f599b1f08b643bcfa16` |

Measurement ID `danekbiglike/rtx3090-20261127-memory-11h`. Local measurements and reduction by the danekbiglike RTX 3090 bring-up project with ChatGPT. Emulator credit: VIctory and fxceless/victory-fork. Please preserve the report ID and link this measurement when reusing the data. The identifier documents attribution when retained.
