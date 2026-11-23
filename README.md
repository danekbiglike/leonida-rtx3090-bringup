# GTA VI Xbox to PC on an RTX 3090 with Leonida

This repository contains two small, independently tested changes for contributors investigating local, offline startup on Windows. The latest RTX 3090 runs passed BVH pipeline creation and reached graphics command submission. A rendered frame and an interactive main menu are still unverified.

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
