# Native 2560×1440 on the RTX 3090

Two Series X trials with the native 1440p override ended in a guest null write. The first reached the prison cell. The second ended during the transition to gameplay. Both used the same SSD copy and save snapshot, with frame generation and upscaling disabled.

| Renderer | Minimum physical RAM available | Time from last present to final memory sample | Stage |
| --- | ---: | ---: | --- |
| Earlier NVIDIA build, a1fb0529 | 3.22 GiB | 59.36 s | Prison cell |
| Indexed buffer planning and head-shape warmup, 70635d00 | 4.34 GiB | 75.00 s | Transition |

The second run used a budget of 8 ms for texture spikes, hot render passes and the NVIDIA launcher's scheduling defaults for streaming workers. Both processes returned 0xc0000005. The launcher recorded zero memory-guard events. The fault sites differ, and these measurements do not establish a common cause. Neither trial produced a timed escort at this resolution.

With the same save snapshot, the second binary completed a two-minute escort to the interview at stock Series X 4K and stock Series S 1080p. [4K results](../4k-guard-escort-and-interview) and [1080p results](../1080p-escort-frame-pacing).
