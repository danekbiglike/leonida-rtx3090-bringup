# Buffer bitsets alone on an RTX 3090

The renderer in this run carries UwUCammie’s buffer descriptor bitset and our adaptation for batched writes on top of the previous heap-owner build. The texture-remap lookup is the original implementation. Its alternative showed no net time saving across the sampled 3D workload in the [two-patch trial](slot-bitsets-escort.md). The renderer passed all 31 descriptor tests. The independent [CPU benchmark](buffer-slot-bitsets.md) uses the same bitset implementation.

| One minute per segment | Frames | FPS | P95 frame | Longest frame | Slowest five seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Waiting for the officer at the cell door | 273 | 4.54 | 277 ms | 357 ms | 4.2 FPS |
| Doorway along the cell corridor | 187 | 3.10 | 519 ms | 1221 ms | 2.2 FPS |
| Along the corridor and through the gate | 190 | 3.17 | 510 ms | 1182 ms | 1.4 FPS |
| Moving inside the common area | 170 | 2.82 | 594 ms | 1093 ms | 1.6 FPS |

The three moving samples recorded 0 of 36 five-second windows at 5 FPS or higher. Screenshots mark the [doorway](bitsets-only/doorway.jpg), the [prison corridor](bitsets-only/corridor.jpg), the [entrance to the common area](bitsets-only/common-area.jpg) and the [last position](bitsets-only/common-end.jpg). Color speckles remain visible on the guard’s arms, and shaded characters remain dark.

The [previous heap-owner run](heap-owner-escort.md) averaged 3.08 FPS in its corridor segment and 2.44 entering the common room. The [two-patch trial](slot-bitsets-escort.md) averaged 3.38 from the doorway to A102 and 2.17 after the gate. This run ended its first minute earlier in the corridor and its second just inside the common area. The different views, workloads and locomotion make the rates descriptive. A repeatable gain over the previous build on a matching walk remains unproven.

The settings XML matched the previous Series X graphics profile byte for byte. The test used the original saved checkpoint, the same keyboard-to-pad mapping and no sampled duplicate texture lookups. All intervals were selected before their measurements. Counts use successful DXGI presents, include whole boundary-crossing frame intervals in the means and assign each present to the five-second bin in which it ended. Stage timers can overlap. [Frame intervals](bitsets-only/present-intervals.csv) · [Per-segment results, five-second counts and stage medians](bitsets-only/segments.json) · [Input times](bitsets-only/input.json) · [Renderer stage counters](bitsets-only/stages.csv)

## Reproduce

Start from the [heap-owner renderer source and stable small-buffer profile](heap-owner-escort.md#reproduce-the-build). Apply the [standalone buffer bitset patch](../../patches/victory-buffer-slot-bitsets-only.patch), then build with Rust 1.98.1. The local executable SHA-256 was `10CF2B2F8BD8E951C3495EBB0A90879D010F1EA2FD702156DBFEEDA00F2E9263`. The only tracked source file that differed from the prior heap-owner renderer was `crates/victory-gpu/src/descriptor/host.rs`. The source patch reverse-applies to the tested build.

```powershell
git apply "$reportRepo/patches/victory-buffer-slot-bitsets-only.patch"
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib descriptor:: -- --test-threads=1
cargo build --locked --profile diag --features diagnostics -p victory
```
