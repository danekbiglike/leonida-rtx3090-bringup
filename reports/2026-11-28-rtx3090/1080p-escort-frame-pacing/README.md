# Series S 1080p escort through the interview on RTX 3090

Lucia left her cell, followed the escort and reached the interview. This run showed **1,987 real frames in 120 seconds, averaging 16.56 FPS**, on the Series S profile with 1920 × 1080 output. The worst five seconds averaged 14.4 FPS and the best five averaged 19.6 FPS. No five-second window reached 25 FPS. The 95th-percentile interval was 74.88 ms and the longest interval was 124.33 ms. The minutes averaged 17.17 and 15.95 FPS. [All presents](frames.csv) · [Five-second counts](metrics.json) · [Before and after](route.jpg)

| Escort through the interview | Series X 4K | Series S 1080p |
| --- | ---: | ---: |
| Real frames per second | 16.18 | 16.56 |
| Weakest five seconds | 10.0 FPS | 14.4 FPS |
| 95th-percentile frame interval | 91.28 ms | 74.88 ms |
| Longest frame interval | 691.04 ms | 124.33 ms |
| Lowest available system RAM | 3.77 GiB | 6.61 GiB |
| Median GPU utilization | 95.5% | 95% |

Both runs used the same renderer binary, starting save, GPU driver, 16 GiB resident ceiling and 120-second forward-input replay. The 1080p start picture is a few steps farther into the room and shows the instruction to wait for the guard. Both ending pictures show the interview. The console profile changes the game's rendering workload along with output resolution. One sample per profile does not establish a repeatable difference of 0.38 FPS. The 1080p recording had fewer long frame intervals. [4K measurements and full-size comparison](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/db9e1fb23185cf17a8e0e27b0a1fca6eb3e95d6b/reports/2026-11-28-rtx3090/4k-guard-escort-and-interview)

In the 1080p interval the median renderer report spent 50.7 ms preparing a frame, including 27.4 ms on buffer copies and 1.8 ms on textures. The copy-back worker reported 15.0 ms per frame. These timers overlap. The median draw count was 2,751 and the median number omitted for missing host pipelines was 355. GPU memory peaked at 12,991 MiB. The separate interval from the cell table to the open corridor averaged 14.33 FPS and its weakest five seconds averaged 12.4 FPS. [Preparation times](costs.csv) · [GPU](gpu.csv) · [Pipelines](pipelines.csv) · [Cell exit](cell-route.jpg) · [Cell frames](cell-frames.csv) · [Cell metrics](cell-metrics.json)

Lighting still has hard boundaries on the face at the desk. The gate, nearby people and office props are visible. DLSS and frame generation were off. Ryzen 7 3700X, RTX 3090, 32 GiB, driver 610.88. Renderer SHA-256 70635d0095783ddd8307b435627f9af829dda78abbd14694015a3ecce96fb211. Measured by danekbiglike with ChatGPT on 28 November 2026.
