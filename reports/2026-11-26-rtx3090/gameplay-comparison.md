# RTX 3090 gameplay comparison

Ryzen 7 3700X with the Series X graphics profile. Values are average FPS. Each number links to frame times, the 95th percentile and the number of frames over 200 ms. Movement routes and NPC positions can differ between runs. See each report for screenshots and controls. [Machine-readable index](gameplay-index.json)

| Renderer build | Facing window | Facing door | With movement keys |
| --- | ---: | ---: | ---: |
| [Paired shaders](paired-waves.md) | [2.58](paired-wave-summary.json) | — | — |
| [Separate copy queue](paired-waves.md) | [3.16](paired-wave-queue-summary.json) | [2.59](paired-wave-queue-room-summary.json) | — |
| [16 KiB transfers](paired-wave-pieces.md) | [3.96](paired-wave-pieces-summary.json) | [2.98](paired-wave-pieces-room-summary.json) | — |
| [Local AVX2 merge](relay-merge-avx2.md) | [4.45](paired-wave-merge-summary.json) | [3.58](paired-wave-merge-room-summary.json) | — |
| [Descriptor refresh](descriptor-refresh.md) | [4.61](paired-wave-heaps-summary.json) | [3.43](paired-wave-heaps-room-summary.json) | [3.22](paired-wave-heaps-moving-summary.json) |
| [Parallel copy-back](parallel-relay.md) | [4.34](paired-wave-land-summary.json) | [3.36](paired-wave-land-room-summary.json) | [3.36](paired-wave-land-moving-summary.json) |
| [Joined readback commands](join-fetch-ranges.md) | [4.43](paired-wave-spans-summary.json) | [3.59](paired-wave-spans-room-summary.json) | [3.41](paired-wave-spans-moving-summary.json) |
