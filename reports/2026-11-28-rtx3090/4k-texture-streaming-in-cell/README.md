# 4K prison cell with the integrated texture streaming changes

The RTX 3090 presented 1,114 game frames in 120 seconds of movement inside the prison cell, averaging **9.28 FPS**. The first minute averaged 7.77 FPS and the second 10.80 FPS. The slowest five seconds averaged 3.0 FPS, and the fastest averaged 16.8 FPS. The 95th-percentile interval was 406.7 ms. [Frame timestamps](frames.csv) · [Timing and memory](metrics.json)

The first capture faces the bookshelf and the last faces the bunk. The run included camera turns, movement and interaction attempts, with additional manual steering and captures. Lucia remained in the cell. The run ends before a verified escort start. The two-minute walk to the interview in the [4K baseline](../4k-guard-escort-and-interview) covers a different workload. The stock player continues to use that baseline. [Start and end captures](route.jpg)

The driver reported median GPU utilization of 96% and average board power of 119.28 W over 59 samples. Free physical memory stayed at or above 3.95 GiB during the window. The harness closed the game on completion. [GPU samples](gpu.csv) · [Pipeline samples](pipelines.csv)

Ryzen 7 3700X, RTX 3090, 32 GiB, Series X output at 3840 × 2160, SSD game and page pool. DLSS and frame generation were off. Renderer SHA-256 `f29915a969ff77ad1fd2e1efc4ca46f9afea6367d26013848edaadb047619cee`. The build combines the revised streaming scheduler, AVX2 comparison and indexed buffer refresh. A causal estimate of the effect of these changes requires a replay with matched movement and camera. [Source patches and tests](../streaming-and-indexed-refresh-integration)
