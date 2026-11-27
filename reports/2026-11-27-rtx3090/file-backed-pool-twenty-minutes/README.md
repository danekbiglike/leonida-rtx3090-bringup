# Twenty minutes of measured game rendering on the RTX 3090

danekbiglike / 2026-11-27 / Ryzen 7 3700X / 32 GiB system RAM / RTX 3090 / existing 3840 × 2160 output profile. The game and the 6.09 GiB file-backed XMem pool were on D. This run used the grouped constant descriptor experiment, release hash 01207dc87710f553de2d92cab1a92ea87630dc77136717a8ef6d296986a02e28.

The process presented beyond minute 20, with no Windows job memory-limit event in this interval. Peak job commitment reached 39.15 GiB under a 42 GiB process limit. Minimum system commit headroom was 8.61 GiB. End-of-minute private memory increased by 212 MB (202 MiB) between minutes 15 and 20. This test does not establish that the growth stops.

Minute 20 contained 551 presents, or 9.18 FPS, with a median 3,777 draw calls. The scene and camera changed during the run. A separate local compilation overlapped the final minutes, which limits performance comparisons. The complete two-minute walking benchmark is published separately. The process was subsequently closed by the operator for another test.

The CSV counts actual presents in consecutive 60-second intervals starting at process boot, including startup. The JSON records the memory accounting scope and limit.
