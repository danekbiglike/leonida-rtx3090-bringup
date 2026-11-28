# Faster ambient-light gather with bit-identical output on an RTX 3090

Changing the gather shader's thread group from **8 × 2 to 16 × 2** reduced the GPU time for one dispatch from about **635 µs to 420 µs** on an RTX 3090. All **691,200 output bytes** matched the original group on both synthetic scenes. Neither the lighting grid nor the sampling equations change. Each of the 160 × 90 points still accumulates all 64 × 36 light cells in the original order. The two call sites dispatch the same total number of points. [Renderer patch](gather-width.patch)

| Scene | Run | 8 × 2 median | 16 × 2 median | 32 × 2 median |
|---|---:|---:|---:|---:|
| 1 | 1 | 634.880 µs | 420.864 µs | 432.128 µs |
| 2 | 1 | 635.904 µs | 420.864 µs | 431.104 µs |
| 1 | 2 | 635.904 µs | 420.864 µs | 432.128 µs |
| 2 | 2 | 635.904 µs | 419.840 µs | 431.104 µs |

The Windows D3D12 harness compiled the renderer's gather HLSL as `cs_5_1`, using the same compiler flags as VIctory. It varied the depth, positions and radiance between scenes. Each width had a warm-up followed by nine samples per scene, rotating the order on each round. GPU timestamps bracket the dispatch and its UAV barrier. Depth and lighting setup, output readback and CPU verification were outside the timed interval. Positive, finite mean-light components were checked on the reference output. Each subsequent result was compared against all reference bytes. The two runs produced 108 timed dispatches. [Run 1](first-run.csv) · [Run 2](samples.csv) · [D3D12 harness](gather.cpp)

The change saved roughly 0.21 ms per tested dispatch. It has yet to be isolated in a whole-game frame-time comparison. The renderer defaults to 8 × 2, with 16 × 2 and 32 × 2 available through `VICTORY_AMBIENT_GATHER_WIDTH`. The RTX 3090 test launcher selected 16 after checking both scenes. The patch applies to the [tested VIctory-NVIDIA revision](https://github.com/trustno1-coder/VIctory-NVIDIA/commit/9a9d5158cc3136b243431c734385a8427e32186a).

On Windows with the Direct3D SDK and the MSVC compiler, build the harness with the supplied command file or compile `gather.cpp` as C++17 with d3d12.lib, dxgi.lib and d3dcompiler.lib. Run `gather.exe <patched-ambient.rs>` on an RTX 3090. The selection script checks the round count, reported byte coverage and paired timings before choosing a width. GPU readback comparisons happen inside the executable. [Build command](build.cmd) · [Selection script](choose_width.py)
