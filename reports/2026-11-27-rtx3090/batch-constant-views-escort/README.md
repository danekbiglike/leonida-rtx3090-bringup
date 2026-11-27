# Batched constant descriptors, 4K prison escort

This run began just through the cell doorway and ended near the grille in the common area. The Ryzen 7 3700X and RTX 3090 presented 981 real frames in 120 seconds. The first minute averaged 10.217 FPS, the second 6.133 FPS and the whole interval 8.175 FPS. The slowest five seconds averaged 0.4 FPS. The 95th-percentile frame time was 166.261 ms, but the longest frame took 4.766 seconds. No five-second window reached 25 FPS.

This build uses the SSD physical pool and batches constant-buffer slot updates. No compiler was running during the marked interval. The preceding 9.10 FPS SSD-pool run began just inside the cell and a compiler was active. Both used the same Series X settings file, 3840×2160 output and native ray acceleration structure builder. Batched updates did not show a reproducible FPS gain in this comparison.

The slowest intervals cluster in the second minute. At +85.49 s the renderer reported 1,460.6 ms of buffer-copy preparation and 0.7 ms of texture preparation per frame in its sampling window. Median buffer-copy preparation across the run was 17.5 ms. Near the longest present interval the card-clock counter reported that the GPU had no queued work for 2,344.8 ms per frame in its window. These samples identify where the renderer spent time. They cannot establish the cause of the wait or implicate descriptor batching alone.

Lighting artifacts remain visible. Peak private commit in the marker window was 35,448,868,864 bytes. The process had no recorded Windows commit-limit event during the interval. The renderer SHA-256 was 01207dc87710f553de2d92cab1a92ea87630dc77136717a8ef6d296986a02e28. Captured and published by danekbiglike with ChatGPT on 27 November 2026.
