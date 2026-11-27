# Title-memory view slots follow their descriptor heap

VI-BR-PORT stores an index and a count for the title-memory descriptor run in each host view heap. At revision `29543253`, the process-wide memory directory indexes that state by the Rust address of the heap. A replacement heap can occupy that address while its D3D12 descriptor slots belong to a different allocation. The old pair then suppresses initialization of the new heap's view slots. Entries for destroyed heaps also remain in the process-wide map. [Original binding path](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/memory.rs#L1028-L1045)

This patch stores the reserved range and populated count on the owning `HostHeap`. Each live heap continues to initialize its range once and populate newly numbered copies in order. A replacement starts empty. No timer, GPU-visible descriptor slot reuse, or live resource eviction is involved.

The regression places two successive real D3D12 heaps at exactly the same Rust address. It reserves the old range for unrelated descriptors in the second heap. Both bindings on each individual heap must agree, and the replacement must return a range disjoint from the unrelated allocation.

## Reproduction and results

Start two separate checkouts of [VI-BR-PORT at 29543253](https://github.com/edsuuu/VI-BR-PORT/tree/2954325320735fa8b56a15e7f3e9654965e3462e). Apply [baseline-control.patch](baseline-control.patch) to the first. It extracts the unchanged binding logic for the test. Apply [heap-directory-owner.patch](heap-directory-owner.patch) to the second. These patches start from the same base and apply independently. In PowerShell, select WARP and run the focused library tests.

```powershell
$env:VICTORY_D3D12_WARP='1'
cargo test --locked --release --config 'profile.release.package.victory-gpu.opt-level=0' --config 'profile.release.package.victory-gpu.debug=0' -j 1 -p victory-gpu --lib --features diagnostics -- memory::tests:: --test-threads=1
cargo test --locked --release --config 'profile.release.package.victory-gpu.opt-level=0' --config 'profile.release.package.victory-gpu.debug=0' -j 1 -p victory-gpu --lib --features diagnostics -- descriptor::host::tests:: --test-threads=1
```

| Revision tested | Scope | Result |
| --- | --- | --- |
| Baseline control | Replacement-heap regression | Failed at the expected overlapping-range assertion |
| Heap-owned range | All three title-memory tests, including replacement | 3 passed |
| Heap-owned range | Host descriptor tests | 38 passed |

The test run used the `diagnostics` feature, which enables VIctory's explicit WARP selection. The two profile overrides reduced compile time for the test crate. The exact result summaries are in [verification.txt](verification.txt).

The separate cap on numbered title-memory copies still applies. The first exhausted copy number during the user's previous long session and the evidence about delayed lists are documented in the [recycling review](../delayed-directory-slot/delayed-directory-slot.md). This fix addresses the per-heap addressing issue. FPS, whole-session memory savings, and where this alias arises in gameplay require separate measurements.

Source and regression identifier `danekbiglike/rtx3090-20261127-heap-directory-owner`. The danekbiglike RTX 3090 bring-up project prepared this change with ChatGPT for VI-BR-PORT. Please retain the identifier and source link when reporting a derivative.
