# Integrated VI-BR-PORT candidate for an RTX 3090 escort test

The Windows x64 release executable is **12,061,184 bytes**, SHA-256 `992f77220e422073b470ce1d21c5b3277d764cb0eafd4af70a407f7bbcc07f0f`. The [manifest](manifest.json) records the six patches in application order, SHA-256 hashes of the eleven modified source files, the toolchain and the benchmark profile. Comparison with the pinned upstream archive found exactly those eleven changed files in the source tree.

The first two patches carry forward the control run's timed input replay, present timestamps and separate game-data directory. The renderer patches remove diagnostic texture-history retention in normal play, add the optional AVX2 relay merge, avoid redundant resource ownership probes and attach title-memory view slots to the descriptor heap that owns them. No game files were used to produce the executable. [Upstream source revision](https://github.com/edsuuu/VI-BR-PORT/tree/2954325320735fa8b56a15e7f3e9654965e3462e) · [Source patch reports and control run](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/177d772bf5ef96145f416c0e07075f84e560117f/reports/2026-11-27-rtx3090)

The candidate uses the same Series X graphics profile for both planned walks. The launcher enables `VICTORY_MERGE_AVX2=1` in both renderer processes and adds the shadow module's counters. The planned comparison changes `VICTORY_CARD_STEPS` from 0 to 1. The release build itself establishes no frame-rate gain, visual parity or long-session memory result.

## Reproduction

Apply the six linked patches in the order in the manifest to VI-BR-PORT `2954325320735fa8b56a15e7f3e9654965e3462e`. The ordinary release build used rustc 1.98.1, the Windows x64 MSVC toolchain and a local copy of the locked dependencies.

```powershell
cargo build --release --locked --offline -p victory --bin victory -j 2
```

The candidate used the same local `dxil.dll` as the measured control, SHA-256 `fda4dde92222ddb8564c3173ce48faa56f7e1c7b46b0b67dada1182ee07a4123`. The executable checksum identifies the artifact used here. Embedded build paths or linker metadata can differ between builds.

Provenance ID `danekbiglike/rtx3090-20261127-integrated-release`. Local build and verification by the danekbiglike RTX 3090 bring-up project with ChatGPT. Individual patch authorship and upstream credits are documented by the linked reports. Preserve these IDs and links when reporting a derivative.
