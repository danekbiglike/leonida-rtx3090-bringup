# RTX 3090 texture readback and render-target XOR addressing

Fifty complete GPU readbacks with a reusable buffer pool took 18.07 ms for a standard 4 KiB tiled texture and 43.01 ms for a 64 KiB render-target XOR texture. The same runs with pooling disabled took 65.39 ms and 81.99 ms respectively. Both modes reproduced the displacement texels and the pitched exposure rows byte for byte. These timers cover the synthetic workload on an RTX 3090 and Ryzen 7 3700X. [Raw GPU test output](gpu-tests.txt)

| Console layout | Pool | Median end-to-end | Median CPU record and reset |
|---|---|---:|---:|
| SW_4KB_S | Off | 1.309 ms | 768.4 µs |
| SW_4KB_S | On | 0.381 ms | 16.4 µs |
| SW_64KB_R_X | Off | 1.627 ms | 803.6 µs |
| SW_64KB_R_X | On | 0.852 ms | 20.3 µs |

The pool and texture ordering changes come from [VIctory-NVIDIA PR 876](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/876), revision 6dc6a5ed2cc8885863455ed8923fcb2f83c851be. Its footprint cache used width, height, depth or array size, mip count and format as the key. A four-layer 2D array and a four-slice 3D volume can share those fields. D3D12 returned four one-slice footprints for the array and one four-slice footprint for the volume. The local key includes the full resource description. A hardware test verifies both shapes and a cache hit for the repeated volume.

[Upstream PR 2879](https://github.com/Marvisak/VIctory/pull/2879), revision 8016b4355cf07eb14439ab97781da9c3498fa112, provides the address equations. I adapted both upload and readback to check the base alignment and the texture shape. The readback still retains a flight dependency until landing for unsupported layouts. Supported cases have one mip, one 2D slice, one sample, two, four or eight bytes per element and a zero base pipe/bank XOR on a 64 KiB boundary. The Series X and Series S tables matched the published AMD address-library hashes on 256 × 256 and 513 × 357 surfaces. All 24 format tests passed, including texel round trips, alignment checks and block coverage. [Format tests](layout-tests.txt)

The GPU test uses a 256 × 256 R32G32_FLOAT displacement texture and two small rows of RGBA32F data with padding. It exercises list recording, GPU execution, retirement, tiling and list reset. The fixture constructs its own bytes. Three earlier prison runs logged a failure to tile an unspecified texture at mip zero, slice zero. Those logs lack the layout and do not establish that this change resolves a particular visual artifact. No gameplay FPS is measured in this report.

The [source patch](render-target-tiling-and-readback.patch) applies to the [measured CPU preparation and half-buffer build](../4k-cpu-preparation-and-face-buffer-trial). Patch SHA-256 is d09ef6017ec6b16b8836596fd2b42c7c17e6b1e48860cafb400a3075094a7c71. The release renderer SHA-256 is 9ff22eb3d07b87a0640aac84d82bf1523701ac8f929d2ef07e4ba3f1638de2f8.
