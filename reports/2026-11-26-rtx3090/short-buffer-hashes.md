# RTX 3090 results with shorter GPU buffer hashes

The Ryzen 7 3700X and RTX 3090 held at least **5.6 FPS in each five-second window** facing the prison window. With the keyboard in the cell, the same session averaged 4.04 and 4.17 FPS. Leaving the cell behind the guard fell to **2.76 FPS**, with a 3.49-second hitch. The previous small-buffer profile reached 3.73 FPS on the corresponding transition. It remains the local shortcut for walking. [Earlier profile and common-room run](small-card-buffers.md)

| Gameplay interval | Frames | Average FPS | P95 frame time | Longest frame |
| --- | ---: | ---: | ---: | ---: |
| [Prison window, 90 s](paired-wave-shorthash-summary.json) | 514 | 5.70 | 200 ms | 262 ms |
| [Facing the door, 60 s](paired-wave-shorthash-room-summary.json) | 255 | 4.24 | 268 ms | 336 ms |
| [Four movement keys in the cell, 60 s](paired-wave-shorthash-moving-summary.json) | 243 | 4.04 | 291 ms | 411 ms |
| [Eight more movement keys in the cell, 60 s](paired-wave-shorthash-route-summary.json) | 251 | 4.17 | 291 ms | 539 ms |
| [Leaving the cell for the corridor, 60 s](short-hash-hall-summary.json) | 167 | 2.76 | 737 ms | 3,491 ms |

The game presented 489 of 514 window frames within 200 ms. All twelve five-second bins of the corridor interval fell below 5 FPS. The last image confirms Lucia reached the corridor. Rectangular lighting bands remain visible in the hair at the door. Colored speckles are visible on the guard's arm in the corridor shot. [Window](short-hash-window.jpg) · [Door](short-hash-door.jpg) · [Second in-cell input interval](short-hash-in-cell.jpg) · [Corridor](short-hash-hall.jpg) · [Frame CSV](short-hash-frames.csv) · [Five-second counts](short-hash-five-second-windows.json) · [Input times](short-hash-inputs.json)

The preceding profile averaged 5.46 FPS at the window and 4.18 at the door. These were separate launches, and the number of draws differed. As an extra check we grouped frames by 50-draw ranges, kept ranges with at least five observations from each run and weighted each by the smaller count. The window then yielded 5.61 and 5.53 FPS with a common weight of only 30. The door yielded 4.24 and 4.23 with a weight of 84. The two runs do not establish an independent gain from the shorter hash. [Draw-count comparison](short-hash-draw-count-bins.csv)

## Reproduce the profile and readback test

Use the same pinned renderer and the same Series X settings as the previous run. The one profile change is `VICTORY_CARD_HASH_LEN=1`. It hashes a buffer through its last occupied 16-byte step. The benchmark used the same executable as the previous profile, SHA-256 `40D05895E7E67A6D567F96D648B42EC92C6440CCF8189EA1764D7651E997C6CF`. [Build recipe](upload-chunks-and-textures.md#reproduce-the-build) · [Short-hash profile](../../profiles/rtx3090-short-buffer-hash.ps1)

```powershell
. .\profiles\rtx3090-short-buffer-hash.ps1 -FrameCsv "$PWD\frame-times.csv"
```

The local D3D12 regression adds a final piece with only 28 occupied bytes to each of two buffers. It verifies the rounded hash length, changed hashes and GPU readback after two submitted updates. It passed in separate processes with 16 KiB and 64 KiB pieces. Apply the test patch on the prepared `Upload4K` checkout. In PowerShell set `$reportRepo` to your reporting checkout and run the following from the renderer checkout. [Regression patch](../../patches/victory-short-hash-partial-piece-test.patch)

```powershell
git apply "$reportRepo/patches/victory-short-hash-partial-piece-test.patch"
. "$reportRepo/profiles/rtx3090-short-buffer-hash.ps1"
foreach ($piece in '16', '64') {
    $env:VICTORY_CARD_PIECE_KB = $piece
    cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib batched_card_hash_preserves_a_partial_final_piece -- --ignored --test-threads=1
    if ($LASTEXITCODE) { throw "GPU readback test failed for $piece KiB" }
}
```

## Why the run stopped

At 06:58 Moscow time on 26 November, the renderer exited after reporting `memory allocation of 4194304 bytes failed`. The wrapper set a 34 GiB process-memory limit. Three seconds before exit the driver reported 13,382 MB of dedicated video memory in use against its 23,557 MB budget. The logs establish a failed allocation. They do not establish whether the process hit its limit or the host exhausted its commit budget. All five measured intervals ended before the crash.

VIctory's upstream contributors implemented the short-hash option. The project owner credits the local code primarily to ChatGPT Astra 6.2 at very high reasoning effort. This repository adds the RTX 3090 profile, test and measurements. [Upstream project](https://github.com/fxceless/victory-fork) · [Local license](../../LICENSE)
