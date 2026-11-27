# Series X prison escort copy waits and an AVX2 port for VI-BR-PORT

During the earlier worker-on escort, the renderer reported a median **84.1 ms** waiting for GPU work before it could read title memory. It also reported **80.9 ms and 94.1 MB** of copy-back per frame. These counters measure overlapping activity. The 120-second worker-off control recorded 105.1 ms waiting and 89.4 ms for 93.1 MB of copy-back. [Original Xbox Series X profile comparison on RTX 3090](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/9ac81a703e6a1c072b4a2ca9c5fe80e84fe62265/reports/2026-11-26-rtx3090/texture-worker-escort)

| Worker | Fill checks with a changed input | Buffer copies with a changed source | Median joinable copies per frame |
| --- | ---: | ---: | ---: |
| Off | 0 of 308 | 330 of 504 | 0 of 26 recorded |
| On | 0 of 404 | 320 of 457 | 0 of 26 recorded |

The [CSV](walk-waits.csv) contains medians of diagnostic reports whose timestamps fall within the recorded two-minute walk. Counts of changed inputs are differences between the first and last cumulative diagnostic reports within the window. Both runs use the same executable. The data show that GPU completion changed the bytes seen by many copies. Skipping waits for those copies could pass stale data to the game.

VI-BR-PORT already includes an alternative for a narrower class of reads. With `VICTORY_RELAY=2` and `VICTORY_CARD_STEPS=1`, supported constant-buffer fills are ordered after their GPU writers. Unsupported resources and dependencies fall back to the original wait. This setting has no measured benefit on this RTX 3090 yet. Upstream's launcher selects stage 2, which additionally moves buffer copies and has a documented case where indexed-texture recording can briefly see earlier bytes. [Stage implementation, ordering checks and limitations](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/host/card_steps.rs#L10) · [Upstream launch profile](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/scripts/play.ps1#L25)

## Relay merge patch

The [rebased patch](vi-br-relay-avx2.patch) applies to `edsuuu/VI-BR-PORT` at `2954325320735fa8b56a15e7f3e9654965e3462e`. The release at that revision still compares incoming GPU bytes with a saved reference using the scalar relay merge. This ports the bring-up project's AVX2 acceleration, with the existing scalar fallback. It changes how the CPU compares already-read bytes. Texture quality, shader selection and GPU synchronization are outside the patch. Set `VICTORY_MERGE_AVX2=1` in the renderer's environment to enable the vector implementation on supported processors.

The previous implementation on an older renderer reduced median copy-back time from 125.8 to 97.8 ms in a stationary prison-window comparison on this Ryzen 7 3700X. The current port's FPS and memory use have not been measured in the game. [Original patch, test conditions and measurements](https://github.com/danekbiglike/leonida-rtx3090-bringup/blob/e605e8858ea851f39af2690aff663d5b88dddc6a/reports/2026-11-26-rtx3090/relay-merge-avx2.md#gameplay-on-the-same-rtx-3090-pc)

The differential tests check unchanged bytes, concurrent title-side changes represented in the input snapshots, unaligned buffers, different input lengths, end regions and the returned change flag. Two standalone tests compiled from the patched source passed with the switch disabled and again enabled on x86-64 Windows. The full renderer and its test targets passed `cargo check --target x86_64-pc-windows-msvc --release --locked --offline -p victory-gpu --tests --features diagnostics` on the clean pinned source with this patch applied. The patch also includes the original opt-in timing fixture.

Provenance ID `danekbiglike/rtx3090-20261127-relay-avx2` appears in the port and walk data. Local patch and measurements by the danekbiglike RTX 3090 bring-up project with ChatGPT, building on the VIctory and VI-BR-PORT relay implementation. Preserve the identifier and link the original and rebased patches when reporting a derivative.
