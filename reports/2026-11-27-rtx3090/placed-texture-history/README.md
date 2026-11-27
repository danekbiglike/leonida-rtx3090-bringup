# Stop retaining placed-texture diagnostic history during play

The renderer stored every distinct texture descriptor with nonzero filler words for the lifetime of the process. The set served one diagnostic counter. On a synthetic workload of 262,144 distinct descriptors, the old accounting retained **26.68 MiB** of Rust allocations. The patched default retained **0 bytes** for that accounting. GPU resources, textures and the renderer's normalized lookup table do not participate in this measurement. [Base revision 29543253](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/resource.rs#L3178)

| Mode | Distinct keys retained | Additional filler variants counted | Live allocation requests, bytes |
| --- | ---: | ---: | ---: |
| Original | 262,144 | 253,952 | 27,979,776 |
| Patched default | 0 | Counter disabled | 0 |
| Patched diagnostic mode | 16,384 | 15,872 | 2,241,472 |

The [patch](placed-filler-stats.patch) removes the diagnostic set from ordinary builds. In builds with the diagnostics feature, setting `VICTORY_PLACED_FILLER_STATS=1` enables a sample of the first 16,384 distinct raw descriptors whose filler was removed. Tracking freezes when the sample fills. Within the sample, repeated requests for the same raw descriptor count once. Variants of different texture shapes or addresses count separately. Census output includes the sample size and limit. The compatibility switch `VICTORY_PLACED_FILLER=1` still keeps the filler words in texture lookup keys.

The original implementation took the history lock inside the resource-map lock and scanned the raw keys for the same address whenever it inserted a new descriptor. The patch leaves texture normalization, the lookup map and its resource lifetimes intact. The optional counter groups variants by address and normalized descriptor, and updates its own lock before texture lookup.

The [overnight RTX 3090 control](https://github.com/danekbiglike/leonida-rtx3090-bringup/blob/dcadbab0eeab12c1eda68a13e5af0769a38368a0/reports/2026-11-27-rtx3090/control-session-ten-hours.md) ran on a different renderer revision that also contained the unbounded counter. Its trace lacks the number of diagnostic keys. The amount retained by this counter during that session and the effect on gameplay FPS remain unmeasured.

## Reproduction

Apply the patch to `edsuuu/VI-BR-PORT` revision `2954325320735fa8b56a15e7f3e9654965e3462e`. Copy [stress.rs](stress.rs) and the patched `crates/victory-gpu/src/placed_filler.rs` into the same temporary directory. From that directory, run these PowerShell commands.

```powershell
rustc --edition 2024 -O --test stress.rs -o stress-tests.exe
.\stress-tests.exe
rustc --edition 2024 -O stress.rs -o stress.exe
Remove-Item Env:VICTORY_PLACED_FILLER_STATS -ErrorAction SilentlyContinue
.\stress.exe original
.\stress.exe default
$env:VICTORY_PLACED_FILLER_STATS = '1'
.\stress.exe opt-in
```

On a clean copy of the pinned source with only this patch applied, `cargo check --target x86_64-pc-windows-msvc --release --locked --offline --lib -p victory-gpu` passed with default features and again with `--features diagnostics`. Both standalone regression tests passed on Windows x64 with rustc 1.98.1.

The harness performs 524,288 calls in each fresh process across 1,024 addresses, eight normalized shapes per address and 32 filler variants per shape. Each descriptor is visited twice. The baseline reproduces the public revision's accounting. Both patched cases call the patched module directly. The allocator wrapper counts requested bytes outstanding above the starting value, which excludes allocator overhead and driver memory. [Exact stress results](stress.csv)

Provenance ID `danekbiglike/rtx3090-20261127-placed-filler` is present in the patch source, optional log output and stress harness. The local change and measurements are from the danekbiglike RTX 3090 bring-up project with ChatGPT. Upstream code and emulator credit belong to VIctory and VI-BR-PORT contributors. Please link the originating revision and preserve the identifier when reporting a derivative.
