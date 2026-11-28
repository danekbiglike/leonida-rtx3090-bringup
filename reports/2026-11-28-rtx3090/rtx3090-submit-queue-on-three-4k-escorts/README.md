# How often the RTX 3090 waited for submission during three 4K prison walks

On three 120-second A-102 escorts, the renderer's device queue was empty for about **13 ms per frame while the CPU submission thread was working**. The thread itself spent 38.85–40.39 ms of CPU time per presentation. A sustained 25 FPS requires completing one new frame every 40 ms. Both measurements point to command preparation as a worthwhile target on the Ryzen 7 3700X. They do not quantify what a different CPU would deliver. [Queue-counter extraction](queue_progress.py)

| Run | FPS | Submit thread CPU per present | Empty queue while submit active | Submit waiting for card | Queue occupied |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Compact staging](../4k-compact-staging-a102-escort) | 17.95 | 39.20 ms | 12.9 ms | 0.1 ms | 77% |
| [4 KiB joined reads](../4k-joined-staging-a102-escort) | 17.27 | 38.85 ms | 13.0 ms | 0.5 ms | 76% |
| [Guarded logging](../4k-filtered-indirect-lock-escort) | 16.95 | 40.39 ms | 13.0 ms | 0.3 ms | 77% |

The last three columns are medians of 115 complete reporting windows per run. Queue occupancy comes from the renderer's own queue accounting. The external GPU utilization monitor samples activity across the adapter and measures a different quantity. CPU time per present uses the Windows thread samples and frame counts from each linked report. Recording and submission overlap GPU execution, so summing these figures does not give total frame time. [Compact staging windows](nvidia-depth-join1137-zero.csv) · [Joined windows](nvidia-depth-join1137.csv) · [Guarded windows](nvidia-depth-log-guard.csv)

An earlier check on this PC changed the console profile and output together. On the same executable and escort through the interview, Series X 4K gave 16.18 FPS and Series S 1080p gave 16.56. The lower-resolution run improved the worst five seconds from 10.0 to 14.4 FPS. The two starting camera positions differed slightly, and the test predates the A-102 results above. [Earlier 1080p and 4K comparison](../1080p-escort-frame-pacing)
