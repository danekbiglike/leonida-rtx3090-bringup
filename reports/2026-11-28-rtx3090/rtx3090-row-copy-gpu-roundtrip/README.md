# Texture row-copy optimization on an RTX 3090

Fifty complete reads of a synthetic 256 × 256 render target using the Xbox XOR address layout took **14.45 ms** on the new build and **43.01 ms** on the preceding build. The median iteration fell from 852.0 to 285.1 µs. Both runs used the same reusable readback buffers. With the standard 4 KiB layout the corresponding totals were 18.07 and 14.58 ms. [GPU test output for both builds](hardware-tests.txt)

| 50 iterations, pool enabled | Earlier total | Row-copy total | Earlier p95 per iteration | Row-copy p95 per iteration |
|---|---:|---:|---:|---:|
| SW_64KB_R_X | 43.01 ms | 14.45 ms | 924.3 µs | 320.7 µs |
| SW_4KB_S | 18.07 ms | 14.58 ms | 591.4 µs | 324.7 µs |

Each iteration exercised the D3D12 readback path with a 512 KiB R32G32_FLOAT displacement texture and two pitched rows of RGBA32F exposure values. The tests verified the displacement and exposure outputs byte for byte on the GPU path. A separate test preserved all 65,536 possible 16-bit patterns through an unsigned buffer view. The prologue previously exercised the same XOR layout with **four bytes per texel**. The displacement texture in this hardware benchmark uses **eight bytes per texel**. [Earlier four-byte CPU test, scene and source patch](../4k-gate-and-xor-row-copy)

These are separate local runs on the same Ryzen 7 3700X and RTX 3090, one 50-iteration series per layout, pool setting and build. They do not establish a frame-rate gain or resolve a particular visible artifact. In the new build, the host also times buffer refreshes taking at least 100 ms. The synthetic readback test exercises the same texture workload as the earlier report. [Earlier test and reproduction commands](../rtx3090-xor-texture-readback)

The new game renderer's SHA-256 is `66a7d1686cf76b3b3bcecb779d91ea57b336ccc37d590574712c61894c253d84`. The tests ran in the corresponding Cargo release test executable.
