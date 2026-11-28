# Three long prison-cell frames on an RTX 3090

Buffer refresh occupied at least 98% of the interval between presents in three independently identifiable frames. Two were consecutive, lasting 7.02 and 5.56 seconds during the approach to the cell door. The GPU queue was empty for most of both. These observations come from the [native 4K run with the reflection limiter](../4k-reflections-cell-to-corridor-gate) on a Ryzen 7 3700X, RTX 3090 and SSD. The original report includes the input window, frames and settings.

| Present interval | Submit thread in buffer refresh | GPU queue empty during submission | Texture refresh across worker threads |
|---:|---:|---:|---:|
| 2,862.9 ms | 2,808.8 ms | 2,606.4 ms | 3.4 ms |
| 7,024.2 ms | 6,931.4 ms | 6,650.8 ms | 3.2 ms |
| 5,561.5 ms | 5,497.4 ms | 5,243.0 ms | 1.9 ms |

The 7.02-second frame requested 10,420 buffer refreshes in 41 batches. Windows recorded six full one-second sampling intervals inside it. Available physical memory at those samples was 5.20–5.24 GiB. The game used 1.25–1.39 logical processors over the last five intervals. Two had zero process read bytes and zero new process page faults. The renderer's aggregate timing includes scanning ranges, updating their contents and waiting for helpers. It cannot identify which of these took the time. [Windows samples](longest-frame-os.csv)

The analysis selects intervals of at least 500 ms whose terminating present lands inside the two-minute cell sample. The first interval above starts before the sample boundary. An interval gets per-stage measurements only if the renderer report follows the present within 5 ms and exactly one present elapsed since the preceding report. Other slow presents are listed with empty timings. GPU queue and CPU measurements overlap in time. [All slow presents](slow-presents.csv) · [Analysis script](analyze.py)
