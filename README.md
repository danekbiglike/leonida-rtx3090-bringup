# GTA VI Xbox to PC on an RTX 3090 with Leonida

Local, offline startup reached the title's own window on a Windows RTX 3090. The latest run passed the Xbox command-list factory and the six-slice depth/UAV allocation, then stopped with a memory access error. All twelve swapchain samples were black, including present 12,527. An interactive main menu has yet to be demonstrated.

## Reproduce the first black frames

Start with a clean checkout of [ladder-frame at b487b6d](https://github.com/ASTROWwwW/Leonida/tree/b487b6d8ccf1d15d723367752a71439c3db077e5). The combined patch contains the source changes used for the run, including the Windows package-read and cache-checker fixes. Apply it once to this exact base.

```powershell
git apply --check ../leonida-rtx3090-bringup/patches/ladder-frame-rtx3090.patch
git apply ../leonida-rtx3090-bringup/patches/ladder-frame-rtx3090.patch
cmake --build build --target gta6rt frame_pacer_test xbox_present_test device_proxy_test
```

Use your usual local package, shader catalogue and matched driver cache. Set `LEONIDA_D3D12=vulkan` and `LEONIDA_FRAME_PROBE=1` in the runner's environment. The probe records attempts, HRESULTs and the number of presented frames. It writes the swapchain pixels for attempts 1, 2, 16 and 128 under the runner's temporary directory when readback succeeds. Each filename gives the width, height and Vulkan format. Format 44 is tightly packed B8G8R8A8_UNORM.

| RTX 3090 observation | Measured result |
| --- | --- |
| Before fixing list CPU handles and sharing frame tokens | First invalid recording call was ClearRenderTargetView. PresentX returned E_INVALIDARG with one plane and the presentation counter stayed at zero through attempt 8,192. |
| After both changes | 10,236 successful list closes, zero failed closes, 9,613 submissions and 4,806 DrawInstanced calls. PresentX passed through attempt 4,096. |
| Full swapchain readback | Each sampled frame was 1,904 × 714. All 1,359,456 pixels in each sample had RGB 0,0,0. |
| Remaining failures in that trial | 49,434 pipeline creation failures accompanied messages for missing vertex and pixel programs. A guest null read terminated this run. Its link to shader availability is unproven. |

The combined patch integrates the driver cache checker [#7474](https://github.com/ItsNotRexed/Leonida/pull/7474), packed texture views [#7604](https://github.com/ItsNotRexed/Leonida/pull/7604), packed stores [#7878](https://github.com/ItsNotRexed/Leonida/pull/7878), command-list CPU descriptors [#7880](https://github.com/ItsNotRexed/Leonida/pull/7880), and the shared frame token source [#7685](https://github.com/ItsNotRexed/Leonida/pull/7685). The integration wires the queue's presenter to the device token source and adapts ExecuteCommandListsX to host command lists. The frame-pacer, Xbox presentation and device proxy tests all passed locally.

### Translate the shaders requested by a trace

With Python 3.11 or later, the helper matches the runtime's missing-program messages to the FSSM files and disassembly in your own working directory. More than one trace can be supplied. The helper prints coverage and the path of a fresh assembly directory. Embedded executable and pipeline-library programs have separate catalogues.

```powershell
python ../leonida-rtx3090-bringup/tools/select_trace_shaders.py "$work/shaders/dxbc" "$trace"
$stage = Read-Host "Assembly directory printed by select_trace_shaders"
python tools/rdna2spirv.py "$stage" --out "$work/shaders/trace-catalog" --no-asm --max-shared-memory 32768 --wave64-emulate --fssm-dir "$work/shaders/dxbc/fssm"
```

## DirectStorage and the next depth attachment

Apply `patches/frame-zlib-srgb.patch` on top of the combined frame patch. It incorporates CPU inflation from [DirectStorage PR 7180](https://github.com/ItsNotRexed/Leonida/pull/7180), the typed sRGB texture handling from [PR 4493](https://github.com/ItsNotRexed/Leonida/pull/4493), storage completion counters, and timed swapchain sampling. The two patches were application-checked in sequence against the pinned base.

With the small shader catalogue held constant, the earlier runtime refused compressed requests. After adding the inflater, request 8,192 completed with 525,316,348 destination bytes delivered across the run and zero failures at that observation. The DirectStorage suite passed 329 checks and the inflater suite passed. The next resource-size failure was a 2D sRGB texture with RTV and UAV flags. With the sRGB change, that allocation passed and the subsequent failure was the Xbox D16_UNORM_S8_UINT depth/stencil format. The focused sRGB/depth comparison matched the host D3D12 runtime. The broader device suite returned a nonzero exit code.

The RTX 3090 reported zero optimal-tiling features for Vulkan D16_UNORM_S8_UINT. D24_UNORM_S8_UINT and D32_SFLOAT_S8_UINT both reported depth/stencil attachment support. A small-catalogue run reached over 65,000 successful presents. All timed pixel samples remained black through that run. Microsoft's DirectXTex identifies the Xbox format in its [texdiag format table](https://github.com/microsoft/DirectXTex/blob/main/Texdiag/texdiag.cpp).

In a separate experiment, 1,061 local shaders translated and passed spirv-val. With the expanded catalogue the NVIDIA driver compiler terminated during startup. A software Vulkan trial also terminated inside the driver. Neither run established a menu.

### Experimental Xbox D16+S8 attachment

`patches/xbox-d16s8-attachment.patch` applies after the two frame patches above. Set `LEONIDA_XBOX_D16S8=1` to enable it. It backs a single-sample, two-dimensional Xbox D16+S8 attachment with Vulkan D32_SFLOAT_S8_UINT, rounds depth clears and fragment depth to UNORM16, and preserves the stencil byte. CPU texture transfers, depth-plane buffer copies and multisample draws for this format are unsupported.

Build `d3d12_depth24_draw_test` with glslang available. On the RTX 3090, `d3d12_depth24_draw_test --xbox-d16s8` passed four 64 × 64 GPU comparisons. Two nearby float values in the same D16 code passed EQUAL at every pixel. Values in the next code failed at every pixel. This held with the generated depth-only fragment stage and an explicit fragment depth output. Each result was verified through stencil readback. The existing D24 draw suite also passed.

With the small shader catalogue, the game passed the former depth allocation. It then exhausted the default 256 MiB GPU address arena while requesting a 90 MiB buffer. Running with `LEONIDA_ARENA_MB=2048` reached a B4G4R4A4_UNORM render-target allocation. The RTX 3090 exposes the corresponding 4-bit Vulkan formats for sampling with no color-attachment feature. The boot samples remained black.

### Packed 4-bit targets and the title window

Apply `patches/frame-b4444-title-window.patch` after the D16+S8 patch. This adds full-surface and rectangle clears for a B4G4R4A4 render target when the GPU can sample its packed format but cannot render directly to it. An R16_UINT backing holds the packed texels. The test reads back all 2,048 texels, including all four channels and a half-step rounding case in the rectangle. Drawing into the emulated format still requires a fragment-output conversion. Such a pipeline returns `E_NOTIMPL`.

The presenter now uses the visible window owned by the title when it exists. The window finder and its fixture come from [NiiRoZz's PR 8591](https://github.com/ItsNotRexed/Leonida/pull/8591). To check the integration in an x64 Visual Studio developer shell, run:

```powershell
cmake --build build --target gta6rt title_window_test d3d12_b5g5r5a1_uav_test
ctest --test-dir build -R "^(title_window|d3d12_b4g4r4a4_rt|d3d12_b5g5r5a1_uav)$" --output-on-failure
```

All three fixtures passed here. On the small catalogue, the title created the packed target, recorded full-screen triangle draws, and presented through its own window. Ten readbacks of 2,564 × 1,061 pixels through present 9,783 were black. The draw samples named one intermediate render target, while successive presents alternated between two other resources. This observation alone cannot establish whether a later copy or composition wrote to the displayed resources. In a repeat, device slot 108 returned an invalid allocation size for a six-slice R16_TYPELESS depth texture with unordered access.

### Depth-array allocation and the first unordered-access layout

`patches/frame-depth-array-sizing.patch` applies after the packed-target patch. It brings the sizing route at Xbox device slot 108 and the creation routes at 127 and 133 into agreement with the existing depth-only fallback at slot 76. It keeps the existing PC flag mask of each route, including tight alignment where supported. The added WARP comparison covers the allocation size, alignment and per-resource record for a synthetic six-slice typeless depth array. The proxy mocks cover both creation routes. Both test executables passed.

This fixes a size query. The following title call asks slot 133 to create the texture in an unordered-access layout. The depth-only backing cannot service shader writes and rejects that request. A separate test suite on this GPU matched WARP in all 46 copy comparisons, including bit-preserving depth-to-color and color-to-depth copies. Those transfers provide a tested building block for synchronizing a storage image with a depth attachment. They do not establish that the two images are synchronized in the game.

### R16 depth and unordered access on Vulkan

Apply `patches/frame-host-import-r16-depth-uav.patch` after the depth-array sizing patch. Its new fixture enters through Xbox device slot 133. For a single-mip, single-sample R16_TYPELESS 2D array created in the unordered-access layout, the Vulkan device now holds a D16 depth image and a separately writable 16-bit image. UAV descriptors and clears use the second image. Transitions into or out of unordered access copy the affected layers bit-for-bit, using the layer's existing depth/color copy path. Shader-resource and depth views use the depth image. The two images consume extra device memory. This path does not alias the texture directly onto the title's CPU address.

```powershell
cmake --build build --target d3d12_xbox_depth_uav_test d3d12_existing_heap_test d3d12_copy_xfmt_test
ctest --test-dir build -R "^(d3d12_xbox_depth_uav|d3d12_existing_heap|d3d12_copy_xfmt)$" --output-on-failure
```

On the RTX 3090 the fixture created two layers, cleared them through separate integer UAVs, used a legacy transition to copy the written data into depth, changed one layer through a DSV, then used an enhanced barrier and a legacy barrier to bring it through storage and back. Four GPU readbacks contained all 2,048 expected 16-bit values. This tests UAV clears and the two transition paths. A compute-shader write and cross-queue ownership are outside the coverage of that fixture.

The buffer-import and existing-heap code comes from [upstream PR 7218](https://github.com/ItsNotRexed/Leonida/pull/7218). This integration keeps the previous texture paths, bounds-checks import arithmetic and requires committed read/write pages for a direct buffer import. The largest observed buffer, 174 MiB, imported successfully. Three smaller imports used the upstream fallback. CPU writes to those original ranges cannot be assumed to reach the fallback buffers.

The new retail run passed the former depth-layout stop. Twelve samples of 2,564 × 1,061 pixels contained zero nonblack RGB pixels. The final sample was present 12,527. The process exited at 28.25 s with a memory access error whose cause is undetermined. At the time of that run the small shader catalogue still lacked 472 distinct requested vertex programs and the runtime refused 2,689 pipeline-library requests. The counts do not establish the cause of the exit. The focused release build passed nine CTest targets plus the separate Xbox D16+S8 comparison.

The last retail measurement preceded a small correction for discard transitions and the addition of a successful-allocation diagnostic. The published revision includes both changes. Its verification was the focused synthetic suite.

### Offline shader coverage after the last launch

On the translator checkout at `ffc6f6da01095e322bd5fcc2aaaf8387cd1c3a87`, `patches/offline-llvm-input-lines.patch` wraps LLVM's input after every 32 bytes. LLVM accepts newlines between bytes, including inside a multiword instruction. A synthetic program with an eight-byte instruction across that boundary produced identical disassembly in both representations.

Processing the compute pipeline library yielded 2,684 programs. Of these, 1,538 assembled and passed the translator's Vulkan 1.2 SPIR-V validation. All 1,538 code/state keys were distinct. The last launch requested 2,680 distinct library code hashes, of which 1,538 occur in this offline index. Target matching by code alone does not verify the state of a particular call. One validator-passing module also carried an LLVM decode warning. The remaining 1,146 source programs produced no validated module in this pass.

The main shader index separately matched all 472 missing vertex programs and 58 of 59 missing pixel programs from the final small-catalogue run. The library extraction, five translation shards and index merge finished in 8 min 21 s. All disassembly files together measured 1.40 GiB. No module from this new library index was submitted to a GPU during this check.

## Reproduce the Windows package-read fix

The test machine hit Windows sharing violation 32 when DirectStorage opened an archive for reading. The successful sharing modes pointed to an existing writable host handle. A synthetic test reproduced the conflict. Repeating the open with read sharing alone reproduced the stop. Allowing the existing writer on the retry let the process initialize its graphics resources.

The patch only retries a failed shared `GENERIC_READ` open of an existing file inside the mounted package. The retry still requests read-only access. The regression test opens a synthetic fixture with a host writer, verifies the bytes read by the title, and checks that a guest request for exclusive access still fails.

1. Clone this handoff repository and [the ladder integration branch](https://github.com/ASTROWwwW/Leonida/tree/ffc6f6da01095e322bd5fcc2aaaf8387cd1c3a87) into sibling directories. Use an x64 Visual Studio developer shell with Ninja and the Vulkan SDK.
2. In the Leonida checkout, run the following commands. The first command selects the exact revision tested here and expects a clean checkout.

```powershell
git checkout --detach ffc6f6da01095e322bd5fcc2aaaf8387cd1c3a87
git apply --check ../leonida-rtx3090-bringup/patches/windows-package-shared-read.patch
git apply ../leonida-rtx3090-bringup/patches/windows-package-shared-read.patch
cmake -S runtime -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DLEONIDA_SDL3_FETCH=ON
cmake --build build --target file_system_test gta6rt
.\build\file_system_test.exe
```

The filesystem test passed all 449 checks on this machine. With this patch, the ladder build reached its first compute pipeline after 1,640 traced Direct3D calls. Without a shader work folder, shader-library initialization was the next stop. The retail measurements used an offline AppContainer and a read-only package mount.

## Inspect the console command list

The other patch is an independent diagnostic for an older Leonida revision. Use a separate clean checkout of [the tested Leonida base](https://github.com/ItsNotRexed/Leonida/tree/6b40d2221cef64c573edd1696d44c2521235bc88). The ladder branch above already has its own command-list implementation.

```powershell
git checkout --detach 6b40d2221cef64c573edd1696d44c2521235bc88
git apply --check ../leonida-rtx3090-bringup/patches/scarlett-list-diagnostics.patch
git apply ../leonida-rtx3090-bringup/patches/scarlett-list-diagnostics.patch
cmake -S runtime -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --target xs_proxy_mock_test device_proxy_test
.\build\xs_proxy_mock_test.exe
.\build\device_proxy_test.exe
```

The patch maps the observed console IID to an Xbox-layout object backed by a host graphics command list. It preserves the two startup extension records in order. If a queue receives a sealed list with untranslated records, the diagnostic stops before submitting the batch. Their GPU effects are still unknown. Both clean-checkout tests passed. The queue test also submitted an ordinary list and waited for its fence.

In separate retail runs on a local runtime with the earlier storage and startup changes, D3D12 and Vulkan each created and closed one direct list and four compute lists. The title then configured frame timing. Those counts describe this diagnostic path. The commands above reproduce the synthetic tests independently of retail files. The related upstream integration and its measurements are in [Leonida PR 7076](https://github.com/ItsNotRexed/Leonida/pull/7076).

## Shader work on the RTX 3090

The local shader build translated all 52 XboxBvhBuilder programs and passed all 52 through SPIRV-Tools validation. The offline Vulkan pipeline checker created all 52 compute pipelines on this device. The following measurements used the same translated programs and three checker workers.

| Cache configuration | Result on the RTX 3090 |
| --- | --- |
| Original checker, cold build | 52 pipelines compiled. The runtime loaded the 5,674,578-byte seed and stopped at the first BVH pipeline after about 32 seconds. |
| Checker with [PR 7474](https://github.com/ItsNotRexed/Leonida/pull/7474), seeded from the first file | The driver reported 52 misses while building. The cache grew to 11,349,216 bytes. |
| Same patched checker, rereading that cache | The driver reported 52 hits, 0 misses, and 0.04 seconds of total compute compile time. |
| Retail run with the updated cache | The loader read 11,349,216 bytes. The title passed BVH initialization and reached command-signature creation at device slot 41 after 1,656 traced D3D12 calls. |

The cache hits in the table come from the checker's driver feedback. The retail result comes from the runtime trace. On this machine, placing the locally generated cache next to the runner allowed the runtime to read it.

```powershell
cmake --build build --target vk_pipeline_check
.\build\vk_pipeline_check.exe "$work\shaders\spirv\bvh" ".\build\pipeline_cache.bin" --jobs 3 --cache-feedback
```

On [ladder-frame](https://github.com/ASTROWwwW/Leonida/tree/b487b6d8ccf1d15d723367752a71439c3db077e5), a trace with only BVH inputs reported 31 missing vertex program hashes. Thirty matched programs in the main shader archive. One matched an embedded executable shader. All ten embedded shaders translated and passed validation. Making those programs available exposed ten additional pixel programs from the main archive. After translating these ten as well, an initial render-path trial no longer reported missing FSSM vertex or pixel programs before its stop. Pipeline-library compute programs are a separate input at device slot 67.

For a full work folder, run the shaders stage on your own local package. Native AMDGPU-enabled LLVM 21.1.8 and SPIRV-Tools 2026.4 were used here. Keep the work directory on a drive with room for the generated outputs.

```powershell
$package = Read-Host "Path to your local package"
$work = Read-Host "Shader working directory"
$out = Read-Host "Output directory"
python make_game.py --game "$package" --work "$work" --out "$out" --stages shaders --wave64-emulate on --jobs 8
```

Upstream maintains its [retail boot coordination thread](https://github.com/ItsNotRexed/Leonida/issues/7154). Relevant work includes [matching the cache checker's device features](https://github.com/ItsNotRexed/Leonida/pull/7474), [seeding the BVH pipelines](https://github.com/ItsNotRexed/Leonida/pull/7586), and [translating the pipeline library](https://github.com/ItsNotRexed/Leonida/pull/7529). The two patches here and these notes were prepared with OpenAI Codex. The included license is Leonida's GPLv3 license.

### Imported shader buffers and exact compute lookup

Apply `patches/frame-typed-imported-views.patch` after `patches/frame-host-import-r16-depth-uav.patch`. It integrates the write-back allocation change from [PR 8458](https://github.com/ItsNotRexed/Leonida/pull/8458) and the typed and structured view decoding from [PR 9068](https://github.com/ItsNotRexed/Leonida/pull/9068) with the Vulkan address lookup in this branch.

The public GPU address still identifies an imported buffer to the title. An SRV or UAV generated by the layer needs the distance from the shader heap base to the actual Vulkan buffer address. A 48-bit unsigned field can encode that distance when the imported buffer is above the base and the range fits. This patch leaves a zero descriptor for an unrepresentable range. It does not implement shader-visible copies for those ranges or for standalone title memory.

On an RTX 3090, a compute shader read all 24 expected values from an imported 4 MiB buffer after the CPU changed its contents following descriptor creation. All 40 out-of-bounds lanes returned zero. The optional positive fixture requires the driver to place this allocation in the encodable range.

```powershell
cmake --build build --target d3d12_compute_test xs_proxy_mock_test xmem_test d3d12_existing_heap_test
$env:LEONIDA_TEST_IMPORTED_SRV = '1'
.\build\d3d12_compute_test.exe
```

In the subsequent title run, all four sampled imports succeeded. The main 174 MiB allocation was below or outside the range the descriptor could encode. Two R16_UINT views of 768 and 6,144 bytes pointed to committed read-write private memory without a registered buffer. The last of 29 black GPU readbacks was present 34,632. At 70.29 seconds the process stopped on a write in VCRUNTIME140. The cause of that write remains open.

`tools/fspx_lookup_check.cpp` runs the runtime's program parser and catalogue lookup on local `.code` and `.state` pairs. It opens the selected SPIR-V module using the same reader as the runtime. The optional third argument writes the matched keys locally. With `LEONIDA_FRAME_PROBE=1`, the runtime also logs both keys for a missing compute program. Compile from a Visual Studio developer shell with `/std:c++20 /EHsc /O2` and add Leonida's `runtime/src` directory to the include path.

The offline checker found exact code-and-state matches and readable modules for 1,538 of 2,684 extracted pairs. The live run requested 2,680 distinct pairs across 2,689 calls. The separately validated catalogue covered 1,538 distinct requested pairs, or 1,543 calls. It was kept offline for this measurement.
