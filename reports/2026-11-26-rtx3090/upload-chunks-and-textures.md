# 4 KiB buffer uploads and partial texture reads on RTX 3090

The [256-byte block experiment](buffer-refresh-and-hitches.md) saved bandwidth but created 4,706 upload ranges per frame. This build allows a wider comparison block in `Shadow::copy_changed`. `VICTORY_UPLOAD_CHUNK_BYTES=4096` compares 4 KiB at once. Equal blocks are skipped and adjacent changed blocks form a single upload. The final short block is clipped to the actual refresh. Only CPU-to-GPU refreshes outside pending shader writes use this setting. The existing 256-byte block size stays the default. Two tests passed, covering fallback values, unchanged bytes, adjacent edges and a short final block. [Local Rust patch](../../patches/victory-upload-chunk-size.patch)

The same experimental binary includes VlREX’s correction for a stale texture hash. A sparse, all-zero read could update the cached hash even though the previous nonzero texture was still on the GPU staging path. A later fully resident zero image could then be skipped incorrectly. The fix records the hash only if the sparse data is accepted. Five texture-memory tests passed locally and the suite skipped one timing test. [VlREX’s upstream PR 395](https://github.com/fxceless/victory-fork/pull/395) · [Port for this build](../../patches/victory-staged-texture-hash-395.patch)

The sync list also includes KyleS98’s batched upload and hash work from PR 1227 with UwUCammie’s readback regression. It issues the buffer uploads together, transitions their resources in one barrier call and then runs the hash passes. The upstream performance result used a 3090 Ti. The local D3D12 regression read back two updated buffers in one submission on the RTX 3090 and passed with both command orders. The performance comparison below toggles upload block selection with batched sync active on both sides. It cannot isolate the gain from command batching alone. [Upstream change and measurements](https://github.com/fxceless/victory-fork/pull/1227) · [Port including the regression](../../patches/victory-batch-card-sync-1227.patch)

## Reproduce the build

```powershell
.\tools\prepare-rtx3090-worktree.ps1 -RendererRepo C:\src\VIctory -Destination C:\src\VIctory-upload -Variant Upload4K
Set-Location C:\src\VIctory-upload
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib chunks_ -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib title_memory_tests -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib two_dirty_card_buffers -- --ignored --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
```

Use the [TextureLOD profile](../../profiles/rtx3090-paired-texture-lod.ps1). Set `VICTORY_COPY_CHANGED=alt` and `VICTORY_UPLOAD_CHUNK_BYTES=4096` to compare full and 4 KiB uploads in one session. Both modes use the same texture fix and journal optimization. The benchmark executable has SHA-256 `40D05895E7E67A6D567F96D648B42EC92C6440CCF8189EA1764D7651E997C6CF`. A second checkout reproduced all 14 changed source files byte for byte after line-ending normalization. The project owner credits the local code primarily to ChatGPT Astra 6.2 at very high reasoning effort.

## RTX 3090 gameplay with 4 KiB upload blocks

A single Series X session alternated whole-range uploads with 4 KiB blocks. Frame intervals use the same one-second switch margin as the preceding 256-byte experiment. The renderer, graphics settings and shade passes were identical across modes. All four physical W, A, D and W presses returned during the movement sample.

| Gameplay interval | Whole ranges, FPS | 4 KiB, FPS | P95, ms (whole / 4 KiB) | Frames within 200 ms (whole / 4 KiB) |
| --- | ---: | ---: | ---: | ---: |
| [Prison window, 160 s](copy-refresh-4k/summary.json) | 4.348 | 4.403 | 271.1 / 265.8 | 59 of 308 / 57 of 313 |
| [Facing the door, 60 s](copy-refresh-4k/door-summary.json) | 3.495 | 3.489 | 341.0 / 327.7 | 0 of 108 / 0 of 76 |
| [Movement, 80 s](copy-refresh-4k/movement-summary.json) | 3.361 | 3.529 | 343.8 / 321.7 | 0 of 118 / 0 of 125 |

The movement sample gained about 5% within this run. Neither mode reached the earlier 3.91 FPS movement measurement on the selected TextureLOD build. An NPC entered the scene during input, and different animation phases can fall into different 20-second blocks. The result at the fixed door was essentially flat. At the window, median uploads fell from 122.4 to 29.3 MB per frame. Median upload ranges rose from 839 to 1,382. The preceding 256-byte build had 4,706 ranges with selective uploads. [Frame CSV](copy-refresh-4k/present.csv) · [Mode switches](copy-refresh-4k/switches.log.txt) · [Stage counters](copy-refresh-4k/stages.csv) · [Analyzer](../../tools/compare_refresh_modes.py)

The sunlit shoulder in the window view has a continuous outer edge. Rectangular bands remain in the hair in the room. The face is lit in the outdoor close-up, but the ground, furniture and portions of the background remain missing. The texture hash regression test establishes that staging values are preserved for the tested sequence. The screenshots alone cannot attribute a visible difference to that change. [Window](upload-window.jpg) · [Door](upload-door.jpg) · [Movement prompt](upload-moving.jpg) · [Outdoor close-up](upload-closeup.jpg) · [Outdoor wide shot](upload-early-scene.jpg)
