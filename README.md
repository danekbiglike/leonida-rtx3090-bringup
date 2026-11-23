# GTA VI Xbox to PC on an RTX 3090 with Leonida

Local, offline startup reached the Vulkan swapchain on a Windows RTX 3090. The driver showed at least 4,096 frames. Four full-resolution readbacks contained only black pixels. The interactive main menu remains unverified.

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
