# Alternating the GPU clock helper in the 4K prison cell

The renderer alternated a background compute workload every 20 seconds on the same RTX 3090. In the four complete, trimmed observation windows in the prison cell, the median GPU clock was 870 MHz with the helper off and 1800 MHz with it on. The observed FPS ranges overlapped. The varying camera and draw count limit how much of the difference can be attributed to the helper. [Phase measurements](clock-turns.csv)

| Helper | Time in cell (s) | FPS | Median draws/frame | Mean board power | Helper CPU time per second |
| --- | ---: | ---: | ---: | ---: | ---: |
| Off | 15–33 | 11.99 | 5799 | 108 W | 8.4 ms |
| On | 35–53 | 11.46 | 6189 | 167 W | 92.1 ms |
| Off | 55–73 | 11.81 | 6347 | 107 W | 9.3 ms |
| On | 75–93 | 13.24 | 6418 | 208 W | 89.2 ms |

The 120-second cell interval contained 1,271 presents (10.59 FPS). Two entire five-second windows had zero presents. A 46.35-second gap began 105.24 seconds into the cell interval and ended at 151.59 seconds, beyond its boundary. The longest interval ending *within* the timed cell sample was 573 ms. Windows had at least 5.55 GiB of physical memory available during that sample. The game later terminated on a null write with the Windows access violation code `0xC0000005`, before reaching the A-102 gate. The trace does not establish why the null write occurred or link it to the helper. There is no escort score from this run. [Cell frames](cell-frames.csv) · [Metrics](cell-metrics.json) · [Boundary-crossing frame](long-frames.json) · [Cell images](cell-route.jpg)

During the long frame, the timer around a 768 KiB buffer transfer recorded 46.15 seconds of wall time. Two mapped reads within it accounted for 22.19 and 23.96 seconds. Between the first and last process samples inside the stall there were 16 hard faults, compared with 14 in the preceding equal-length window. Reads on the disk hosting the page file averaged 0.08 MiB/s during the stall. This trace identifies where a thread waited; the exception diagnostic also appeared while these timers were open, so they cannot isolate the initiating fault. [Recorded buffer timers](long-frames.json)

The test used the same renderer executable as the [17.62 FPS reference escort](../4k-prison-depth-and-write-audit), Series X settings, 3840 × 2160 output, a Ryzen 7 3700X and 32 GiB of system RAM. No frame generation or DLSS was enabled. The comparison uses complete transitions logged by the renderer, drops one second from each end and counts actual presents over the remaining wall time. Each row has nine GPU samples. Windows CPU deltas are included only when their full sampling interval is inside the trimmed window. [Analysis script](compare_clock_turns.py) · [Board samples](cell-gpu.csv)
