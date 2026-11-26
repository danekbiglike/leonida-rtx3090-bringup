# Dedicated texture thread on the RTX 3090 during the prison escort

Ryzen 7 3700X, RTX 3090, Windows, Series X profile. The same executable ran twice, first with the texture worker enabled and then disabled. The worker is the indexed-texture upload pass from [fxceless’s upstream change](https://github.com/fxceless/victory-fork/commit/d4a528ba08c92214a106392c65e645ba298263f9).

| Walk interval | Worker off | Worker on | Off / on five-second windows averaging at least 5 FPS |
| --- | ---: | ---: | ---: |
| First 60 seconds | 3.37 FPS | 3.87 FPS | 0/12 · 0/12 |
| Second 60 seconds | 3.07 FPS | 3.57 FPS | 0/12 · 0/12 |
| Full 120 seconds | 3.22 FPS | 3.72 FPS | 0/24 · 0/24 |

Across 120 seconds, the off/on p95 frame intervals were 506/420 ms. The slowest five seconds averaged 1.2/2.0 FPS. The worker posted nonzero activity during 105 reporting windows in the enabled arm, with a median 48.2 ms of reported work per frame. The disabled arm logged 0 such windows.

Both runs reached the common room. The enabled run entered it earlier on the replay. The prison wall texture, clothing detail, floor reflections and gate are visible in both. Bright light patches at the cell door and overly dark figures in the common room persist in both modes. The character positions, poses and shading differ between captures. These samples show no obvious new loss of texture detail. The first scheduled control screenshot was saved about three seconds after the marker. This does not affect the frame counts. The two-minute rate rose by 15.5 percent in this pair, from 386 to 446 presents. Neither arm sustained 5 FPS.

Both runs started with byte-matched copies of the same save, graphics settings, and shader/pipeline cache. The measured walk began at the cell door with the officer present, 515.699 seconds after the first frame with at least 1,000 draw calls, to the nearest millisecond in both runs. For 120 seconds the game’s keyboard-to-pad input received W for 350 ms every 550 ms. No other movement keys were sent during measurement. The fps values count completed presents in fixed wall-clock windows. The pictures were captured on the same schedule. The two runs were sequential and the positions on the route were not frame-locked.

[Paired starting views](paired-000.jpg) · [30 seconds](paired-030.jpg) · [60 seconds](paired-060.jpg) · [90 seconds](paired-090.jpg) · [Finish](paired-121.jpg). [All counts and percentiles](metrics.json) · [Off frame intervals](off-presents.csv) · [On frame intervals](on-presents.csv).

## Build and verification

Start with the [standalone bitset renderer](../bitsets-only-escort.md), then apply the [renderer patch](../../../patches/victory-texture-worker-3090.patch). Set VICTORY_HEAP_WORKER to 1 or 0 and keep late waits enabled as in the previous profile. The optional [measurement patch](escort-capture-and-input.patch) records UTC timestamps and drives the route when VICTORY_ESCORT_MARK points to a file containing its UTC start in milliseconds. The original launcher constructs an explicit child environment, so the worker switch must reach the renderer process. The tested executable had SHA-256 `3c3252b05fc0c328b41dcab0b3f679567db459822ed36835201b59cf59529994`. The worker source file matches the revision reporting the [RTX 4070 boat result](https://github.com/fxceless/victory-fork/blob/e4245f3c1b0490250d9cf0946a2113000be98687/README.md).

The GPU library suite passed 218 tests, skipped 10, and failed one indirect-draw WARP budget assertion. The same assertion also failed on the unmodified local baseline. The measured runs used the physical RTX 3090.
