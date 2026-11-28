# CPU time per presented frame on three RTX 3090 prison escorts

Windows thread accounting puts the single submission thread at **37.25–40.92 ms of CPU time per presented frame** across three 4K runs from A-102 into the dayroom on a Ryzen 7 3700X. Sustaining 25 FPS gives a single thread 40 ms of elapsed time per frame, including waits. The six command-list recording threads together consumed another 146–149 ms of CPU per frame. They run concurrently. The refresh workers together consumed 25–26 ms. A faster refresh alone would still leave very little time on the submission thread for waiting or more complex frames.

| Run | Seconds sampled | Presents in complete intervals | Submission ms/frame | Six list threads combined | Refresh threads combined |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Ordered uploads](nvidia-order.csv) | 119.01 | 2,067 | 40.92 | 148.71 | 26.38 |
| [Depth audit](nvidia-depth-audit.csv) | 118.29 | 2,081 | 39.88 | 149.42 | 25.82 |
| [Grouped buffer refresh](nvidia-depth-refresh-groups.csv) | 119.06 | 2,012 | 37.25 | 146.15 | 25.05 |

The calculation sums user and kernel time reported by Windows for each named thread. Every included sampling interval lies entirely within the 120-second route. The denominator counts actual presents within those same intervals. Differences at the two boundaries explain the smaller frame counts here than in the full route scores. The absolute thread times can overlap each other and GPU work. This measurement identifies where CPU time was spent, without identifying an individual function or predicting an FPS gain. [Analysis script](phase_recording_cpu.py) · [Depth audit route and raw presents](../4k-prison-depth-and-write-audit) · [Grouped route](../4k-grouped-front-refresh-escort)
