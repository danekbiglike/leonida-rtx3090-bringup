# Joining adjacent GPU readbacks on the RTX 3090

The RTX 3090 trace shows thousands of 16 KiB pieces fetched every frame. This local patch records adjacent pieces as a single Direct3D 12 copy when they belong to the same buffer and their source and destination offsets are both contiguous. The CPU still checks and merges every piece in its original order. It applies to both the direct queue and the separate readback queue. The switch defaults off. [Exact renderer patch](../../patches/victory-join-fetch-ranges-rtx3090.patch)

## Verification and reproduction

Apply the [parallel relay patch set](parallel-relay.md) and then this patch. The differential unit test compares every expanded source and destination byte against the original command sequence, including a missing source range, a destination gap, two separate resources of the same value and an empty list. That test and ten relay tests passed. The test executable has SHA-256 `85EF756FF3FB623FA31028A6B68F6361D5681931110697A8F4D7FAF9E55F48A1`.

```powershell
$patch = (Resolve-Path ../leonida-rtx3090-bringup/patches/victory-join-fetch-ranges-rtx3090.patch).Path
git apply --check $patch
git apply $patch
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib fetch_range_tests
cargo build --locked --profile diag --features diagnostics -p victory
$env:VICTORY_JOIN_FETCH_RANGES = '1'
```

The diagnostic line `relay readback per frame` reports source pieces and D3D12 commands separately. The project owner credits this local patch primarily to ChatGPT Astra 6.2 at very high reasoning effort. The underlying readback and queue code belongs to its upstream authors.


For the complete renderer source use the [preparation script](../../tools/prepare-rtx3090-worktree.ps1) with `-Variant Joined`. In a fresh checkout this reproduced every changed source file from the local build. To enable the measured code path, use the AVX2 profile from the parallel relay report, set `VICTORY_WIDE_MERGE=1` and `VICTORY_JOIN_FETCH_RANGES=1`, and forward both variables to the renderer.
