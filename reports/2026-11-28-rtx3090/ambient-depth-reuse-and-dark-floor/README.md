# Reusing the sampled depth in the indirect lighting passes on an RTX 3090

The gather already calculates depth at each point of its 160 × 90 lighting grid. Writing it next to the three light coefficients lets the diffuse and reflection passes reuse that value for each of their four surrounding points. This adds 225 KiB to the point buffer. The gather is rebuilt from the current depth immediately before either consumer. Its UAV barrier orders the writes. The change leaves the occlusion, normal, weighting and color equations intact. [Renderer patch](cached-depth.patch)

On a native D3D12 fixture, **every output pixel and all 995,344 cell-buffer bytes matched the original** on two generated scenes at each resolution. At 3840 × 2160 the diffuse output comparison covers 33,177,600 bytes. The corresponding reflection uses a half-size R11G11B10 image and covers 8,294,400 bytes. The odd-size case also exercises clamping at the right and bottom edges.

| Depth resolution and output pass | Original gather and pass | Cached depth | Cached depth with 16 × 2 gather |
| --- | ---: | ---: | ---: |
| 2560 × 1440, diffuse | 1.866 ms | 1.839–1.841 ms | 1.736–1.738 ms |
| 2560 × 1440, reflection | 0.730 ms | 0.718 ms | 0.613–0.614 ms |
| 3840 × 2160, diffuse | 3.432–3.433 ms | 3.391–3.393 ms | 3.288–3.290 ms |
| 3840 × 2160, reflection | 0.807 ms | 0.790–0.791 ms | 0.684–0.687 ms |

Values are medians of the combined gather and output dispatch times across both scenes in each run. Each variant ran seven paired, alternating timed rounds per scene at three sizes, plus warm-up. GPU timestamps include the UAV barriers. Input generation and output readbacks are outside the timestamps. There were **672 timed samples across four runs**. With depth reuse alone, the diffuse pair at 4K saved about 40 µs. Most of the combined improvement came from the wider gather. These measurements do not establish an in-game frame rate. [Per-scene medians](medians.csv) · [Depth reuse runs](first-run.csv) · [Replication](replicate.csv) · [Wider gather](combined-1.csv) · [Wider gather replication](combined-2.csv)

## Testing a floor for very dark rooms

A separate run compared a 0.05 minimum diffuse light level with the default of zero, using the upstream floor after the clamp on the game's existing light. At 4K the two bright synthetic scenes kept **all 8,294,400 diffuse pixels** each. All diffuse pixels in the deliberately dark scene changed. The comparison checked that every changed pixel originally had a component below the floor within packing precision, and that no color component decreased beyond that precision. All reflection pixels stayed identical in all three scenes. This tests the shader's rule. A game capture is still needed to judge the appearance of the prison and skin. [Pixel counts](floor-check.csv) · [Upstream lighting floor by s0ngo73](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/475)

## Reproducing the comparison

Build the C++17 fixture on Windows x64 with the Windows SDK and MSVC. It selects the RTX 3090 by adapter name and compiles the source shaders with D3DCompile as cs_5_1. The original inputs use the VIctory-NVIDIA indirect-light implementation and our earlier measured branch. The wider gather is the previously tested 16 × 2 variant. The Rust files preserve the emulator source used in the comparisons. [VIctory-NVIDIA](https://github.com/trustno1-coder/VIctory-NVIDIA) · [License](https://github.com/trustno1-coder/VIctory-NVIDIA/blob/main/LICENSE) · [Fixture](light_depth.cpp) · [D3D12 support](d3d_test.hpp)

```bat
cl /nologo /std:c++17 /EHsc /W4 /O2 light_depth.cpp /link d3d12.lib dxgi.lib d3dcompiler.lib
light_depth.exe baseline-ambient.rs cached-ambient.rs
light_depth.exe baseline-ambient.rs cached-ambient.rs 16
light_depth.exe floor-ambient.rs floor-ambient.rs 16 floor
```
