# RTX 3090 prison escort with SSD-backed physical pages

Measured by danekbiglike on 27 November 2026. Lucia started in the cell facing the officer at the open door and reached the common area. The route contact sheet at 0, 60 and 121 seconds comes directly from the game window. The Series X settings file, 3840×2160 output, native ray acceleration structure builder, eight translation workers and streaming switches matched the earlier 4K streaming profile. The new physical pool backed 6,538,919,936 bytes on the SSD.

During the 120-second input replay the renderer presented 1,092 frames. The average was 9.10 FPS, the slowest five seconds averaged 4.4 FPS, p95 was 212.3 ms and the longest frame was 1.402 seconds. None of the 24 five-second windows reached 25 FPS. The median draw count was 5,263.5. The GPU reported median utilization of 80.5% and peak VRAM use of 15,098 MiB. Lighting artifacts remain visible.

Private committed bytes rose from 35,752,710,144 to 36,028,596,224. Available system commit stayed above 15,739,428,864 bytes. Median preparation time was 64.1 ms, including 19.8 ms in buffer copies and 1.1 ms in texture work. Separate CPU and GPU counters overlap. A low-priority Rust compiler was active in the timed interval. Both the route and concurrent CPU load differ from the earlier 9.27 FPS result. These measurements cannot isolate a frame-rate effect of the pool.

Executable SHA-256 is 5ddc4f14297533d16d5fc6a753e582dfcd90ae1804eb5f316df475d0a4ca41ac. Game files and save data are excluded from this report.
