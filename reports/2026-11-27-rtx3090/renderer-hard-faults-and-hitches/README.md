# Process hard faults during long frames on the RTX 3090

In 161 matched intervals of approximately one second, 53 spent at least half their time between presents separated by 500 ms or more. VIctory had a median 35.02 hard page faults per second in this group. In 94 intervals that spent no time in a gap that long, the median was 4.485. The remaining intervals were mixed. The game had advanced from the prison to a scene with the aiming tutorial.

Median disk reads during the two groups were 5.47 vs 2.10 MiB/s on D: (game and SSD pool) and 0.18 vs 0.13 MiB/s on E: (Windows paging disk). These disk counters cover all processes. The hard-fault counter covers the renderer alone. Neither tells which file backed a particular fault or which renderer thread waited. This observation supports investigating page-in stalls, without establishing which drive or which code change caused them.

Sampling used Windows SystemProcessInformation and checked the renderer's PID, image name and creation time. Only this renderer's fault and cycle counts were retained. The join script computes the fraction of each interval covered by long present gaps, including seconds with zero presents. It matches the nearest disk sample within 600 ms. The executable, graphics settings and measurement machine match the batch-constant-views-escort report. Recorded by danekbiglike on 27 November 2026.
