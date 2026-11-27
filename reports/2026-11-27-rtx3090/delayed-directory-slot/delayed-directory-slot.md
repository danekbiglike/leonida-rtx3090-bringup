# Reusing title-memory descriptors after eight frames

On the RTX 3090 Series X control run of November 26, 2026, VIctory logged its first exhausted title-memory copy number at 18:50:23.944757 UTC, about 32 minutes after launch. The run used 2,047 numbers. The warning says new pages without a number read as zero. The game continued. This observation alone cannot identify which pixels were affected or explain the process's commit growth. Build and route details are in the [RTX 3090 control report](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/9ac81a703e6a1c072b4a2ca9c5fe80e84fe62265/reports/2026-11-26-rtx3090/texture-worker-escort).

The inspected [VI-BR-PORT revision](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/memory.rs#L300-L321) keeps 4,095 numbers. SpaghettiMaster545's [earlier recycling patch](https://github.com/fxceless/victory-fork/commit/b26d793bfcaf01b4b803ec9c19b094ff85faf393) quarantines a number for eight title frames before rewriting its descriptor. On this VI-BR revision, a title frame counts a completed frame wait. That counter does not prove that a particular closed command list has been submitted or completed. [Frame counter](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/frame.rs#L82-L85)

## Delayed command list on Windows WARP

The [standalone control](delayed-directory-slot.cpp) records two dispatches into one command list. Both read an SRV containing `0x30900001`. The program closes the list, signals and waits for sixteen real D3D12 queue fences with that list held, and changes the first descriptor to a resource containing `0x30900002`. It then submits the held list and reads back both results. The descriptors are declared volatile and updated before submission, as allowed by the [D3D12 root signature contract](https://learn.microsoft.com/en-us/windows/win32/direct3d12/root-signature-version-1-1#descriptors_volatile).

Run [check-delayed-directory-slot.cmd](check-delayed-directory-slot.cmd) on Windows with the Visual C++ build tools and the Windows SDK. The control needs no game files.

```text
danekbiglike/delayed-directory-slot-v1 WARP completed_before_submit=16 reused=0x30900002 retained=0x30900001
```

Exit code 0. One list recorded against two identical inputs read two different values after its first slot was reused. A guarantee based on age or an unrelated completed fence is insufficient to preserve a still-recorded list's bindings.

## Additional porting constraints

- The older patch clears pages by comparing a directory word directly to the slot number. VI-BR adds a high read-only flag to that word. A direct transplant would leave those pages pointing at the recycled number. The target's lookup masks the flag. [Directory encoding](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/memory.rs#L846-L859)
- The current target also has GPU-owned structure pages inside arenas. Some have no complete copy in title RAM. Reclaiming by host-visible root accesses alone could discard the only correct page. [Arena ownership](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/memory.rs#L44-L61)
- A compatible implementation must account for retained recordings, including a list that is discarded or submitted again, and complete every GPU use before overwriting its physical descriptors. Queue-ordered directory publication has been demonstrated separately. It does not itself reclaim exhausted numbers. [Queue-order proposal and its WARP test](https://github.com/fxceless/victory-fork/commit/55cf6c7ffd6293549108f16fef993793d33cb19c)

The eight-frame patch did not apply against this revision and was excluded from the gameplay candidate. The standalone result tests the lifetime assumption. It does not measure FPS, reproduce faulty game rendering or establish that the long-session memory leak is fixed.
