# GTA VI Xbox to PC on an RTX 3090 with Leonida

## RTX 3090 gameplay reports

**RTX 3090 with small GPU buffers.** The controllable prison window averaged **5.46 FPS** for 90 seconds, with at least 26 presents every five seconds. Facing the door averaged 4.18 FPS. Leaving the cell and following the guard into the common room averaged 3.73 and 2.90 FPS. Bands remain in the hair. [Profile, source recipe and screenshots](reports/2026-11-26-rtx3090/small-card-buffers.md) · [Five-second counts](reports/2026-11-26-rtx3090/small-card-five-second-windows.json)

The buffer-refresh experiment on the RTX 3090 cut traffic by 81% while FPS stayed at 4.33. The report includes a reusable interval analyzer and a separate Rust patch for redundant CPU work. [Frame times, source and reproduction](reports/2026-11-26-rtx3090/buffer-refresh-and-hitches.md)

The earlier TextureLOD profile on the Ryzen 7 3700X and RTX 3090 measured **4.66 FPS at the window, 3.93 at the door and 3.91 with keyboard input**. An additional minute averaged 2.76 FPS and included a 3.38 s stall. [Reproduce this build](reports/2026-11-26-rtx3090/descriptor-locks-texture-mips.md) · [PowerShell profile](profiles/rtx3090-paired-texture-lod.ps1)

Compare the measured renderer builds at the prison window, facing the door and during keyboard input. [FPS comparison](reports/2026-11-26-rtx3090/gameplay-comparison.md) · [JSON for tools](reports/2026-11-26-rtx3090/gameplay-index.json) · [Reproduce the builds](reports/2026-11-26-rtx3090/parallel-relay.md#prepare-the-exact-renderer-sources)

On the RTX 3090, the paired-wave build removes the large blocks on the sunlit shoulder at the prison window. With GPU memory tuning and our AVX2 write-merge patch, the window reached **4.45 FPS**, up from 2.58 FPS. Facing the door, the same build measured **3.58 FPS**. [Verified profile, patches and gameplay data](reports/2026-11-26-rtx3090/relay-merge-avx2.md#gameplay-on-the-same-rtx-3090-pc) [Reusable PowerShell profile](profiles/rtx3090-paired-avx2.ps1) The original texture test averaged 3.39 FPS before and 3.42 FPS after. Reports include matched screenshots, source pins, patches and per-frame data. [RTX 3090 gameplay report and patch](reports/2026-11-26-rtx3090/README.md) [RTX 3090 square lighting artifact tests and gameplay frame data](reports/2026-11-26-rtx3090/lighting-trial.md) [Paired-wave RTX 3090 gameplay comparison](reports/2026-11-26-rtx3090/paired-waves.md)


The Xbox build opens its own window on a Windows RTX 3090. With on-demand graphics compilation it now submits two draws into an intermediate texture and a third into the surface it presents. The final pass now has a verified view of the intermediate texture. Both surfaces are still black in the sampled frames. Leonida still has no verified interactive menu on this machine. On VIctory the same PC now reaches the game's full Settings screen and switches tabs with the keyboard. The tested route is below.

## Native Windows menus with VIctory

On the same RTX 3090, VIctory rendered the offline profile prompt, the animated introduction and the Russian first-run settings. The game responded to controller A, and a normal keyboard Enter advanced between the navigation, text-size, subtitle and brightness screens. The initial settings persisted locally. The window reported about 30 fps on these screens. The first settings run later exhausted allocations while loading, with a per-process commit limit of 16 GiB. That early test covered the menu and loading sequence.

This was a separate D3D12/DXIL runtime built from [VIctory at 97c78d1](https://github.com/Marvisak/VIctory/tree/97c78d1087808bd6ce5eabb5d566083a38406a90). Our local run used its Series X mode, an offline AppContainer, a read-only package, external cache and profile directories, and store licence queries configured to report offline. The first profile selection in the measured run used VIctory's built-in diagnostic A-button input. Later settings changes were verified with real window input. At the same setup stage, a Series S comparison rendered black in the sampled frames on this machine.

The [window input patch](patches/victory-window-pad-input.patch) captures mapped controller keys received by the game's own window, including brief taps between input polls. Releasing the key or losing focus clears held input. The optional `VICTORY_KEYBOARD_PAD=1` also maps keyboard buttons to the first attached pad. Native analog inputs stay intact. All eight GameInput tests passed on Windows. The [separate content-root patch](patches/victory-separate-content-root.patch) lets an executable staged outside its data folder mount the configured package on the virtual game drive.

### Open the full Settings screen from a fresh profile

Confirmed on native Windows with an RTX 3090 in Series X mode, using the game's Russian UI. The game rendered the **Control Scheme** tab, the Xbox controller illustration and its action labels. Pressing E switched to **Controller**, where the camera sensitivity settings were visible. Q returned to **Control Scheme**. The runtime reported about 30 fps here. A local 1920 × 1080 capture and the input trace confirmed the result. With a previously initialized profile, startup went from the profile prompt through the introduction and loading artwork. Later runs on the same PC reached the controllable prison room, documented in the gameplay reports above.

1. Use the [pinned upstream build instructions](https://github.com/Marvisak/VIctory/tree/97c78d1087808bd6ce5eabb5d566083a38406a90#readme) and a locally available game package. From the VIctory checkout, apply the two patches linked above and then the [keyboard-only patch](patches/victory-keyboard-only.patch). The last patch adds a per-process option to ignore physical controllers while using the normal keyboard-to-gamepad mapping.
2. Build with `cargo build --locked --profile diag -p victory --features diagnostics`. Choose an empty writable directory for `VICTORY_DATA_DIR` to see first-run setup while preserving other profiles. Set `VICTORY_GAME_DIR` to the content root, `VICTORY_CACHE_DIR` to a writable cache and `VICTORY_KEYBOARD_ONLY=1` for this keyboard test. The measured run also applied the [offline store patch](patches/victory-offline-store.patch) before building. It reports package and game licence queries as unavailable in this offline configuration. Input was entirely manual in this run.
3. Launch the title using the upstream `run <exe> --execute` entry point. At the PLAYER prompt use Enter (A). After the intro, use Enter to advance through navigation, text size, subtitles and brightness.
4. On **Finish setup?**, press **Esc** (Xbox Menu). This opens Settings. **Q / E** switch tabs (LB / RB), the arrows move the selection, and **Backspace** goes back (B). The observed tab strip included Control Scheme, Controller, Gameplay, Display, UI and Camera.

### Identify the compute shader from the actual first bind

The independently measured VIctory first bind selected a single compute container. Its recorded byte length and 64-bit BLAKE3 prefix matched exactly one container in the local package extraction. Its source SHA-256 independently matched a request in the Leonida trace. The 8 × 8 × 1 Vulkan translation passed SPIR-V validation. Adding only that module to the graphics catalogue gave Leonida a matching compute entry on a repeat run. That 26-second run ended before a dispatch was observed. This identifies the active program without substituting an arbitrary pipeline.

Install the Python `blake3` package and put `spirv-val` on PATH. Supply a VIctory diagnostic log with first-bind events and a Leonida log with the compute-request probe. This prints the uniquely matched module name on your own machine. To repeat the one-module experiment, copy the graphics catalogue to a new sibling folder and add that module's SPIR-V file and unmodified metadata entry from the full translation index. Keep the original native graphics map and the deferred graphics setting.

```powershell
python tools/match_active_compute.py --victory-log $victoryLog --leonida-log $leonidaLog --dxbc $dxbc --translated $translations
```

## Where black enters the frame

On an RTX 3090, bounded samples of the game's first two intermediate draws already predict black RGB. In four inspected first-pass draws the three vertices formed a nondegenerate triangle. All three vertex colors were opaque black, and the pixel stage forwarded that color. In ten inspected second-pass draws the vertices were white, but the pixel stage multiplied them by a zero uniform. These are measurements of CPU-authored inputs at submission time. Fragment coverage and the reason the game selected those inputs remain open.

The generic input probe reports readability, nonzero values and exact ones for up to three vertex colors and the first four float4 constants. The controlled upload-buffer draw and its default-buffer variant both matched all 4,096 expected GPU pixels. The upload path reported the three expected red colors. The probe marked the default-buffer vertex data unreadable. A separate local analysis decoded the first pass's own buffer format. That game-specific decoder and the original inputs are outside this repository.

In another 26-second run, all 56 observed compute dispatches used 5 × 5 × 33 groups and the same root layout. The title supplied a null pipeline at command-list reset and never supplied one through SetPipelineState before those dispatches. The catalogue had missed 1,050 distinct compute programs requested against that layout. The layout and group count alone do not identify which program the title intended.

The runtime also rejected the game's 3D unordered-access view. The volume patch implements a full-depth 3D view at a selected mip, including the default descriptor and the explicit all-remaining-slices form. A restricted W slice range remains unsupported and produces a null descriptor. In a fresh 26-second run, Vulkan registered the game's 33 × 33 × 33 RGBA16F storage view at mip zero. The game submitted 304 draws, 101 into the display sources. Four full intermediate reads, two full display-source reads and seven swapchain samples still contained zero nonblack RGB pixels.

### Reproduce the input and volume checks

Apply these after the [static table-span patch](patches/frame-shader-table-spans.patch), in this order. Use the settings for on-demand graphics below. The tests build their own fixtures.

```powershell
git apply ../leonida-rtx3090-bringup/patches/frame-authored-draw-inputs.patch
git apply ../leonida-rtx3090-bringup/patches/frame-dispatch-inputs.patch
git apply ../leonida-rtx3090-bringup/patches/frame-volume-uav.patch
cmake --build build --target gta6rt d3d12_draw_test d3d12_compute_test d3d12_descriptor_test vk_bindless_test
ctest --test-dir build --output-on-failure -R '^(d3d12_descriptor|d3d12_compute|vk_bindless_ps_imgatomic)$'
./build/d3d12_draw_test.exe --upload-vertices
```

The descriptor fixture checks both ways of naming the entire depth at mip one, the default view at mip zero and five rejected ranges. The Vulkan atomic fixture separately verified all 64 voxels of a 4 × 4 × 4 volume. All three CTest fixtures passed. Look for `volume-uav` with `registered=1` in a local run with `LEONIDA_FRAME_GRAPH=1`. The input probe uses `input-snapshot`, `vertex-color` and `constant-prefix`. The `dispatch-input` probe records pipeline and layout availability at the call. [Microsoft's definition of a 3D UAV](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_tex3d_uav).

## On-demand graphics and the first draw to the display

On the same PC, the small catalogue used one GPU pipeline configuration for 159 submitted draws in a 22-second run. Every draw targeted the intermediate surface. The extended catalogue produced the following results.

| RTX 3090, native Windows | Measurement |
| --- | --- |
| Local catalogue preparation | 6,047 additional vertex and pixel modules passed `spirv-val --target-env vulkan1.3`. Three failed validation and were excluded. The main index held 6,089 entries and the native map held 6,045 distinct digests. The separate embedded and BVH catalogues brought the indexed total to 6,151. |
| Xbox device slot 57, 27-second run | The loader accepted 7,967 of 25,450 requests, up from 216 with the small catalogue. It refused 17,483 and used zero stubs. Acceptance in this mode retains a validated recipe on the CPU. Vulkan compiled three graphics configurations for the actual draws. |
| Where the frame went | Of 532 submitted draws, 355 targeted the same intermediate surface and 177 targeted the two alternating display sources. All nine swapchain RGB samples through present 225 were black. The harness stopped the process on time. |
| Independent 25-second repeat | 439 submitted draws, including 146 into the display sources. All eight swapchain samples were black. Six full-resolution 3,840 × 2,160 target reads, including one of each display source, contained zero nonblack RGB pixels. The harness stopped the process on time. |
| Alpha and bindings in the repeat | In the intermediate target, all 8,294,400 pixels had nonzero alpha after the first sampled submission. Three subsequent reads had exactly 4,147,200 pixels with nonzero alpha. In both display source reads all alpha was zero. The later two pipelines each consumed three vertex attributes from bound slot 0, had full color-write masks and used one root table in argument word 8. |

Each target read happens **after the entire submission**. Multiple draws in the same submission can affect the measurement. These observations reproduce the three-draw frame seen on Wine/RDNA2 and narrow the RGB loss to the intermediate surface or earlier. They leave open what the composition shader actually sampled. [Independent Wine/RDNA2 measurements](https://github.com/ProjectLeonida/Leonida/issues/8851#issuecomment-7115442902).

### Reproduce on a 32-lane GPU

Start with the ladder base, nine integration files and 15 patches through [the recorded-draw probe](#before-submission), using the order documented below. Apply the next two patches on top. Module sharing is adapted from [the integration shader-module cache](https://github.com/ASTROWwwW/Leonida/commit/0c08b73638d6eaddfeb43257b6008e61c85c7fdc). The new deferred path retains post-link shader words and builds modules and attachment-specific pipelines on the first compatible draw. Compute uses the original catalogue.

```powershell
git apply ../leonida-rtx3090-bringup/patches/frame-on-demand-graphics.patch
git apply ../leonida-rtx3090-bringup/patches/frame-composition-inputs.patch
cmake --build build --target gta6rt d3d12_draw_test d3d12_depth24_draw_test d3d12_compute_test shader_module_cache_test
python ../leonida-rtx3090-bringup/tools/prepare_draw_catalog.py --leonida . --base $smallCatalog --translated $translatedGraphics --dxbc $dxbc --output $drawCatalog --validator spirv-val
$env:LEONIDA_DEFER_GRAPHICS = '1'
$env:LEONIDA_SHADERS = $drawCatalog
$env:LEONIDA_FRAME_GRAPH = '1'
$env:LEONIDA_FRAME_PROBE = '1'
```

Use the 42-entry base catalogue described below for `$smallCatalog`. Supply your own full translated directory with its wave metadata for `$translatedGraphics`, and the local DXBC directory for `$dxbc`. Set `$drawCatalog` to a new sibling directory on the same drive as the DXBC files. The loader needs read access to both. The [preparation tool](tools/prepare_draw_catalog.py) makes independent shader copies and adds only conventional vertex and pixel stages marked subgroup 32 or wave-emulation class A/B. Launch with the game and runner settings used for the earlier title-memory run, including `LEONIDA_D3D12=vulkan`, `LEONIDA_ARENA_MB=2048`, `LEONIDA_XBOX_D16S8=1` and `LEONIDA_SHADOW_LOW_IMPORTS=1`. Keep deferred compilation enabled for the expanded catalogue.

The draw, depth, compute and module-cache tests passed with deferred compilation both on and off. The draw fixture matched all 4,096 expected pixels and built 37 configurations on demand. The Xbox D16+S8 fixture passed in deferred mode. A second preparation of the local catalogue matched all 6,159 output files byte for byte.

### Reading descriptor tables written by the title

Apply [the descriptor backing patch](patches/frame-title-table-pull.patch) after the composition-input probe. On this ladder the queue had a hook for reading a table from the title's own memory, but the Xbox descriptor-heap proxy never registered a source. The proxy now copies complete slots from a live, registered backing into its corresponding Vulkan heap before submission. It checks memory access and clamps to the registered allocation. The new mock covers a CPU-written slot, an explicit null, incomplete and misaligned requests, a read crossing the end and a request following heap release.

On the same extended catalogue, before this fix, all 66 sampled table scans found an allocated, entirely zero 32-byte slot. The first 20 recorded bindings in the two later drawing passes could each be correlated with one of these scans. With the callback connected, all 65 sampled scans copied one slot from the title and every slot became nonzero. None of those first slots was an image descriptor. The 25-second run submitted 75 draws into the presentation sources. All six swapchain samples and all six 4K target reads remained black in RGB. The Xbox device proxy, title-address alias, GPU title-address and pixel draw tests passed.

The current root-signature scan covers one declared slot on both later passes. Offline inspection of the active translated draw programs shows that the final pass reads additional slots from the same table. Whether those entries have reached the shader-visible heap is the next measurable distinction. The earlier command-list interface issue is already passed by all of these runs. Xbox device slot 73 requests `C3827890-4024-474C-98CF-645B51DC4874`, which the loader maps to the Windows `ID3D12GraphicsCommandList6` interface. [Command-list mapping in the pinned loader](https://github.com/ASTROWwwW/Leonida/blob/b487b6d8ccf1d15d723367752a71439c3db077e5/runtime/shims/d3d12_xs_command_list_iid.h).


### Which texture the display pass can see

Apply [the static table-span patch](patches/frame-shader-table-spans.patch) after the descriptor backing patch. The translator now records the span of statically located scalar loads from an unadjusted, zero-extended root-table pointer. The bound graphics pipeline combines the spans of its shader stages. At recording time the list applies them only to an actual resource-table parameter. The queue still clamps copies to a currently registered shader-visible heap.

Four active graphics modules were translated again locally and all passed Vulkan 1.3 SPIR-V validation. The catalogue tool accepts optional metadata from a second translation only when the original program digest, shader stage and complete SPIR-V file match. Two byte-identical stages supplied new table metadata. All Vulkan shader binaries used in the comparison stayed the same.

In a 26-second Windows RTX 3090 run the game submitted 157 draws, 52 of them into its two presentation sources. Ten distinct display-pass table handles were correlated with bounded scans. **All ten contained a registered view of the actual intermediate render target, at mip 0 and array layer 0.** Across 31 sampled scans of three slots, all three slots were populated and the middle slot matched the bindless image table every time. All four complete intermediate reads, both complete display-source reads and five swapchain samples had zero nonblack RGB pixels. These CPU-side matches establish the texture contents available to the shader. The measurements do not count individual GPU texture fetches.

To reproduce, regenerate translations with the patched translator using the original translation options. For pre-existing modules use the optional `--metadata-from $updatedTranslations` argument to [the catalogue tool](tools/prepare_draw_catalog.py). Keep the graphics settings described above. Run the [composition summary](tools/summarize_composition.py) on the local runtime log to count table matches and RGB readbacks without outputting handles.

```powershell
git apply ../leonida-rtx3090-bringup/patches/frame-title-table-pull.patch
git apply ../leonida-rtx3090-bringup/patches/frame-shader-table-spans.patch
cmake --build build --target gta6rt shader_library_test d3d12_draw_test
python -I tests/test_shader_meta.py
python ../leonida-rtx3090-bringup/tools/summarize_composition.py $runtimeLog
```

The shader library and draw fixtures passed. All 28 shader metadata tests passed, including the static span and dynamic-offset regression. The remaining RGB question starts in the two intermediate draws. Both source and presentation textures were already black at the sampled submissions.


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

### Shader-visible copies of title memory on RTX 3090

Apply `patches/frame-title-memory-windows.patch` after the typed-views patch. It incorporates [PR 8225](https://github.com/ItsNotRexed/Leonida/pull/8225) and [PR 9137](https://github.com/ItsNotRexed/Leonida/pull/9137). Two changes are specific to this integration:

- `LEONIDA_SHADOW_LOW_IMPORTS=1` requests a refreshed GPU-side copy when a successful host import has an address outside the descriptor's 48-bit range. The title retains its own address. Copies are refreshed from CPU memory before submissions. GPU-to-CPU coherence for general writable resources is still an open limitation.
- Xbox device slot 70 can encode a typed or structured SRV for a registered title allocation with no placed resource. It checks that the complete view fits a translated arena range before encoding it. The device retains the underlying storage.

On the RTX 3090, `d3d12_title_va_test` read all 64 expected values through a manually written buffer descriptor, a created constant-buffer view and a root view. The standalone slot-70 fixture encoded a 384-element R16_UINT view and rejected an address outside the registered allocation. The existing-heap, compute, proxy, address-range and 198-check memory suites passed.

In the title, slot 70 created a 3,072-element R16_UINT view and a structured view. The 174 MiB buffer went through the arena-copy path. Its first timed refresh took 19.96 ms. The last of 44 black GPU readbacks was present 508. The run stopped on a write in VCRUNTIME140 at 114.46 seconds. The refresh cost is paid on every submission. This run did not display a menu.

```powershell
cmake --build build --target d3d12_title_va_test title_va_alias_test gta6rt
$env:LEONIDA_SHADOW_LOW_IMPORTS = '1'
.\build\d3d12_title_va_test.exe
.\build\title_va_alias_test.exe
```

### Graphics root arguments and the retail draw

Apply `patches/frame-graphics-root-registers.patch` after the title-memory patch. This integrates [PR 9014](https://github.com/ItsNotRexed/Leonida/pull/9014) and [PR 9276](https://github.com/ItsNotRexed/Leonida/pull/9276) while retaining the descriptor counts used to scan bound tables. Graphics arguments start at s8, each table takes one dword and the bound heap bases follow the arguments.

On the RTX 3090 the draw fixture matched all 4,096 pixels. The direct heap-index fixture verified 384 compute results and 192 pixel-shader texels, including bindings changed between dispatches and indirect execution. The root signature, compute, title-memory and depth fixtures also passed.

With the same small shader catalogue and shadow settings, a subsequent title run submitted draws and produced 44 GPU readbacks. All 2,720,404 sampled pixels were black in each readback through present 488. The run stopped on a write in VCRUNTIME140 after 110.76 seconds. These are sampled presents. The relationship between the process stop and the missing pipelines remains undetermined.

```powershell
cmake --build build --target root_signature_test d3d12_draw_test d3d12_heap_index_test
.\build\root_signature_test.exe
.\build\d3d12_draw_test.exe
.\build\d3d12_heap_index_test.exe
```

The heap-index target requires llvm-mc, spirv-as and spirv-val when configuring the build.

## Draw target and storage completions

Apply these patches in order after the graphics root-register patch.

1. [Submitted draw-target readback](patches/frame-submitted-target-readback.patch) adds an opt-in readback of the first color target after successful submissions containing draws 1, 2, 8 and 32. It also counts explicit copies, resolves and clears in the first 4,096 submitted batches. Set `LEONIDA_FRAME_GRAPH=1` for this measurement and `LEONIDA_FRAME_PROBE=1` for the existing swapchain measurement. Readbacks serialize GPU work and may affect timing.
2. [Descriptor writeback](patches/frame-title-descriptor-writeback.patch) incorporates AAyberkU's [PR 9586](https://github.com/ItsNotRexed/Leonida/pull/9586), extends writeback to this branch's device slot 70, and checks that the destination is writable. The mock tests cover a typed buffer descriptor and its neighboring bytes.
3. [DirectStorage completion trace](patches/frame-storage-completion-trace.patch) ports [gautch29's trace patch](https://github.com/ItsNotRexed/Leonida/issues/8851#issuecomment-7114972782). Pass `--trace boot.jsonl` to the local runner. Join the `dstorage` events by `queue` and `entry` to distinguish queued, submitted, started and completed commands. The trace also records the completion HRESULT.

On Windows with an RTX 3090, the same 102-entry shader catalogue and the title-memory shadows enabled, the 52-second run ended at the configured time limit.

| Observation | Measurement |
| --- | --- |
| Color attachment after submissions containing draws 1, 2, 8, 32 | 0 of 8,294,400 pixels with nonzero RGB each time. The 64×64 draw fixture produced 3,840, 3,840 and 4,096 colored pixels using the same probe. |
| PresentX readbacks | 22 samples through present 253. All 2,720,404 sampled pixels in each were black. |
| Resource identities | One sampled draw target and two alternating presentation sources. The observed submissions contained 162 color clears and no explicit resource copies, texture copies or resolves. Shader reads are outside this counter. |
| Descriptor writeback | At least 8,192 writes observed, with 32-byte descriptors at the last logged milestone. |
| DirectStorage | 9,746 file requests and 335 statuses reached all four phases and completed successfully. No pending entries at the cutoff. File completions ran from 3.698 s to 51.172 s, with 16 in the final five-second bin. No fence or event entries were recorded. |
| Process I/O | Windows `GetProcessIoCounters` reports 157,007,690 read bytes at 5 s, 1,084,573,604 at 20 s and 1,127,151,554 at 52 s. The total was flat at the 30, 35, 40 and 45 s samples and advanced again by 50 s. These are all process reads. |

A preceding 35-second run using the draw-target probe without the descriptor-writeback patch also returned black from all four target reads. Both runs used a small shader catalogue. The remaining pipeline misses and the relationship between the draw target and the two presentation sources are still open. The local ladder base also forwards Xbox device slot 57 to the PC lifetime-tracker method. The [slot-57 graphics pipeline implementation](https://github.com/ItsNotRexed/Leonida/pull/8890) addresses that different ABI.

Validation included the native draw, heap-index, device-proxy, Xbox proxy mock and title-VA fixtures, 337 DirectStorage checks and 22 Python trace tests. All twelve patches applied in sequence to the pinned ladder base. Build the shader fixtures with LLVM and SPIRV-Tools available at configure time.

## Native graphics pipelines and the missing presentation draw

The older ladder proxy forwarded Xbox device slot 57 to the Windows lifetime tracker. This port uses the integration branch's native graphics pipeline decoder and hash index, keeps PSO streams for derived pipelines at slot 55, and creates streams through the queried `ID3D12Device2` at slot 86. Credit goes to enx and the contributors to the [pinned integration tree](https://github.com/ASTROWwwW/Leonida/tree/1812e0bd1ee1bfc54006edcc1e400e91d5cdd57f).

Start in the ladder checkout with the twelve patches above applied. The nine files below are byte-identical to the integration revision.

```powershell
$integration = '1812e0bd1ee1bfc54006edcc1e400e91d5cdd57f'
git fetch https://github.com/ASTROWwwW/Leonida.git $integration
$files = @(
    'runtime/src/native_pso.h',
    'runtime/shims/d3d12_xs_native_pso.h',
    'runtime/shims/d3d12_xs_pso_stream.h',
    'runtime/shims/d3d12_xs_pso_stream.cpp',
    'runtime/test/native_pso_test.cpp',
    'runtime/test/xs_native_pso_test.cpp',
    'runtime/test/pso_stream_test.cpp',
    'tools/native_pso_hashes.py',
    'tests/test_native_pso_hashes.py'
)
git restore --source=$integration --worktree -- $files
git apply ../leonida-rtx3090-bringup/patches/frame-native-graphics-pipelines.patch
git apply ../leonida-rtx3090-bringup/patches/frame-draw-pipeline-routing.patch
cmake --build build --target gta6rt native_pso_test xs_native_pso_test pso_stream_test
python -I tools/native_pso_hashes.py $dxbc $smallCatalog
```

`$dxbc` holds the local DXBC containers. `$smallCatalog` is the 40-entry main graphics catalogue with its embedded and BVH subfolders. Set `LEONIDA_SHADERS` to that catalogue, enable both frame probes, and leave pipeline stubs disabled.

| Measured on the RTX 3090 | Result |
| --- | --- |
| 40 graphics digests, 102 total shader entries | At the sampled submission the runtime had handled 25,450 requests through slot 57, created 180 real pipelines and refused 25,270. Zero stubs. |
| First 256 native requests matched offline to original containers | 252 requested a vertex and a pixel stage, four requested just a vertex stage. Two missing pixel programs each occurred with an available vertex program 18 times. Both passed SPIR-V validation for Vulkan 1.3. |
| 42 graphics digests, 104 total shader entries | 216 pipelines created and 25,234 refused for the same 25,450 calls. The gain of 36 matches the two request groups. All four 4K color-target reads and all 24 sampled presents through present 262 were black. The process stopped on a write in VCRUNTIME140.dll at 56.99 s. Its cause remains undetermined. |
| Separate 27-second run with draw routing enabled | 164 submitted draws in 164 draw-containing batches used one vertex/pixel pair and one intermediate target. Neither added fragment program was bound on those draws. The two presentation sources received 165 clears between them. Neither was the first color target of any submitted draw. All 11 swapchain samples through present 231 were black. The harness stopped the process on time. |

The [catalogue extension tool](tools/extend_native_graphics_catalog.py) matches the first 256 traced native requests offline. It copies the two highest-frequency missing class-A wave64-emulated pixel programs with an available vertex program. With the baseline trace its output matched every file in the trial catalogue byte for byte.

```powershell
python ../leonida-rtx3090-bringup/tools/extend_native_graphics_catalog.py --leonida . --dxbc $dxbc --translated $fullCatalog --preferred $translatedGraphics --base $smallCatalog --log $runtimeLog --output $newCatalog --validator spirv-val
```

`$fullCatalog` supplies the full translation index for offline matching. `$translatedGraphics` holds the translated graphics modules and wave64-emulation metadata. `$runtimeLog` is the small-catalogue run's diagnostic stderr. Use a new directory for `$newCatalog`. The RTX 3090 runs used the small catalogues.

A contributor using a full catalogue on Wine/RDNA2 measured two intermediate draws followed by a draw into the surface passed to PresentX. On this ladder run, the observed command stream lacked that final draw. The target and pipeline probes let another implementation compare the composition draw and its input surface. [Full-catalogue draw trace](https://github.com/ProjectLeonida/Leonida/issues/8851#issuecomment-7115442902).

The native decoder, native proxy, stream, existing Xbox proxy and Windows device proxy tests passed. The four native-map Python tests passed. The instrumented draw fixture matched all 4,096 pixels. All fourteen patches and nine pinned files replayed successfully against the original ladder base.

### Before submission

Apply [the draw-input probe](patches/frame-recorded-draw-inputs.patch) after the routing patch. With both probes enabled it records the first 4,096 draw attempts before validation and a mask of populated shader argument words for submitted draws.

In another 27-second run, all 229 observed draw attempts selected the same intermediate surface as their only color target. All had a graphics pipeline, root layout and triangle-list topology. Neither presentation source appeared as a target at the recording boundary. The 160 submitted draws used the same stage pair as before. Only argument word 8 was nonzero. Eleven swapchain samples through present 225 and all four intermediate readbacks were black. These counters cannot establish why the title did not issue the other passes on this stack.

Matching Microsoft's public symbols for the locally loaded Windows runtime identified the longer run's faulting routine as `memset`. It attempted a write near null. Five earlier saved traces had the same routine and the same first two title call sites. This identifies the operation and leaves the origin of the invalid destination open.
