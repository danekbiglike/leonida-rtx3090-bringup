# 16 KiB readback and GPU memory on RTX 3090

**3.96 FPS at the prison window and 2.98 FPS looking into the room.** The same scenes previously measured 3.16 and 2.59 FPS with the queue profile. The original paired-wave window measurement was 2.58 FPS. We measured accepted DXGI presents; the faster profile still exceeded 200 ms on every frame.

| Player-controlled scene | Length | Frames | FPS | P95 | Longest frame | Mean draws per frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prison window | 90 s | 357 | 3.96 | 283.4 ms | 309.5 ms | 4,870 |
| After turning to the door | 60 s | 181 | 2.98 | 385.3 ms | 620.0 ms | 6,860 |

The large blocks along the sunlit shoulder remained absent in both angles. The switch to the room exposed a transient dark door material that became light grey during the test. Some block-shaped highlights within the hair and dark patches on the floor and partition remain. The outdoor cutscene has separate rendering issues. [Window](paired-wave-pieces-window.jpg) · [Room before settling](paired-wave-pieces-room.jpg) · [Room after settling](paired-wave-pieces-room-warm.jpg)

The primary interval was selected at elapsed 740–830 seconds. Keyboard input after that interval turned Lucia into the room; the second sample spans elapsed 900–960 seconds. Median diagnostic copy-back time at the window fell from 162.3 ms in the queue run to 125.8 ms, and the reported GPU wait fell from 156.5 to 98.8 ms. Ten system samples before timing recorded 1,725–1,998 MiB of available RAM. [Window CSV](paired-wave-pieces-frames.csv) · [Window JSON](paired-wave-pieces-summary.json) · [Room CSV](paired-wave-pieces-room-frames.csv) · [Room JSON](paired-wave-pieces-room-summary.json)

## Reproduce

The test used the same Ryzen 7 3700X, RTX 3090 24 GB, 32 GB of RAM, native Windows, saved checkpoint and Series X graphics settings as the [queue comparison](paired-waves.md#separate-copy-queue-and-batched-draw-submission). The baseline renderer uses paired wave64 translation, preserved throughout these tests.

1. Apply the [paired-wave renderer patch](../../patches/victory-rtx3090-paired-waves.patch) to base `1ffff57a192c8a225118ae946ab21635c38442be` following the [build instructions](paired-waves.md#reproduction).
2. Use the [exact upstream PR 1164 diff used for this run](../../patches/upstream-pr1164-readback-pieces.patch). UwUCammie authored the upstream change. It makes the GPU compare and transfer plan operate on configurable pieces; the original size was 64 KiB. [Upstream pull request](https://github.com/fxceless/victory-fork/pull/1164)
3. From the renderer checkout, run the following in PowerShell, with the report repository checked out alongside it. Three WARP shader tests and seven buffer-span tests passed here.
   
```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/upstream-pr1164-readback-pieces.patch).Path
git apply --check $patch
git apply $patch
$env:VICTORY_CARD_PIECE_KB = '16'
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib warp_card_ -- --test-threads=1
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib shadow::card_tests -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
```

Dot-source the [16 KiB profile](../../profiles/rtx3090-paired-16k.ps1) in the launch session. Pass `-FrameCsv .\frames.csv` for a fresh measurement. It uses the queue profile plus `VICTORY_CARD_PIECE_KB=16`, `VICTORY_CARD_WINDOWS_MB=2048` and `VICTORY_LEVELS_ON_DEMAND=1`. This is a combined profile comparison. The latter two options allow selected buffers to reside in dedicated GPU memory and allocate texture levels when the game holds them. The upstream [memory experiment on a different PC](https://github.com/fxceless/victory-fork/blob/32b31f753427704111c021353c33f198f622ff9b/README.md) motivated using spare VRAM. The local binary SHA-256 was `6B2E052C29A80691BD742988F79CFCF86FC4690FA767AA44C249628C0C1906F6`.

The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for local renderer changes, integration, tests and measurements. Upstream changes remain attributed to their authors.

The subsequent AVX2 implementation on the Ryzen 7 3700X measured 4.45 FPS at the same window and 3.58 FPS facing the door. [CPU patch, profile and gameplay results](relay-merge-avx2.md#gameplay-on-the-same-rtx-3090-pc)
