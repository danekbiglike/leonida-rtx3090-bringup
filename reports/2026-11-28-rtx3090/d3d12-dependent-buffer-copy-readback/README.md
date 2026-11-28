# Readback of four dependent D3D12 buffer copies on RTX 3090

Using whole-buffer enhanced barriers with COMMON access on both sides left **191–192 incorrect bytes out of 2,048** after four dependent copies. Naming COPY_SOURCE and COPY_DEST and scoping the copy side to SYNC_COPY returned all 2,048 bytes correctly for each of five initial patterns. Both the CPU mapping and an independent GPU copy to a readback heap gave the same counts. Driver 610.88, Windows, GeForce RTX 3090. [Raw counts](samples.csv)

| Ordering | Five runs, incorrect bytes per run |
|---|---|
| Complete each copy with a queue fence | 0, 0, 0, 0, 0 |
| Global enhanced barriers, COMMON access | 0, 0, 0, 0, 0 |
| Resource-scoped enhanced barriers, COMMON access | 192, 192, 192, 191, 192 |
| Resource-scoped enhanced barriers, explicit copy access | 0, 0, 0, 0, 0 |

The native test initializes two independent 1,024-byte buffers with different bytes. It records four 64-byte copies, alternating the buffers so each copy reads the preceding result. It checks both entire buffers against a CPU reference after the fence. Every configuration uses the same five inputs. The program requires enhanced barriers and selects an RTX 3090 explicitly. It runs without game data. [Source](verify.cpp) · [Build command](build.cmd) · [Direct3D buffer barrier fields](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_buffer_barrier)

A local VIctory hardware test caught the stale-byte problem before the first experimental renderer entered the game. The revised renderer scopes a wait only for two distinct, independently backed shadow buffers and specifies the access of both source and destination before and after each copy. Shared guest mappings, copies within one resource, and unsupported devices retain the original global ordering. This narrower experiment was inspired by [VIctory-NVIDIA PR 799](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/799). The native experiment supplies a data-integrity result. Gameplay FPS and visual differences require a separate measurement. [Patch against the indexed RTX 3090 baseline](copy-barriers.patch)
