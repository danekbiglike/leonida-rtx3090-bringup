# Release unregistered title-memory allocations on failure

The Windows allocator kept 64 MiB committed when the renderer failed to create an arena shadow. Directory initialization could also leave a 16 MiB mapping committed. Repeated arena requests with a full descriptor table still attempted allocation. Three regression tests reproduced these failure paths on Windows. With the fix all six tests in the memory module passed. [Test results](verification.txt)

The patch checks for a free slot before allocating a new arena. A reservation owns the Windows allocation until the renderer publishes its address. Dropping an unpublished reservation releases its commit. The directory allocates its fault buffer before registering the address. Existing descriptor numbers remain usable at capacity. Successful published mappings retain their existing lifetime. [Patch and tests](arena-rollback.patch)

Apply this patch after the six patches in the [integrated renderer](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/00ee6ff54e400e1391419abc9e070467dbcb346a/reports/2026-11-27-rtx3090/integrated-release). The patch passed `git apply --check` against that source. The tests exercise failure injection with the D3D12 WARP adapter on Windows. The frequency of these failure paths during gameplay and their contribution to the earlier out-of-memory exit remain unmeasured.

Regression and patch ID `danekbiglike/rtx3090-20261127-title-memory-rollback`. Local tests and patch by the danekbiglike bring-up project with ChatGPT, on top of VI-BR-PORT and its upstream contributors.
