# Alternating all sixteen logical processors and one per physical core

The test queried the actual Windows topology of the Ryzen 7 3700X. In the same running process it alternated the original sixteen-processor affinity with eight logical processors, one per physical core. Each change was followed by five seconds of warmup and a 30-second present count. The script restored and verified the original mask after the last interval. No global CPU settings were changed.

The five consecutive intervals averaged 10.800, 10.299, 0.367, 4.700 and 4.967 FPS, respectively. The game changed scenes on its own and draw counts varied during the test. It had advanced beyond the prison to a different scene with an aiming tutorial by the next visual observation. This prevents a causal comparison of scheduling policies. Neither mask delivered a stable 25 FPS. The player profile uses the original Windows affinity.

Measured by danekbiglike with ChatGPT, 27 November 2026. The timestamps are UTC microseconds. The original mask was 0xffff and the one-per-core mask was 0x5555.
