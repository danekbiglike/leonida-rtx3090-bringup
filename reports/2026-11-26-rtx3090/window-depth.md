# Prison-window depth test on RTX 3090

**Result: 2.97 FPS over 90 seconds in the controllable prison scene.** The shoulder still showed square steps after enabling early depth for the glass pass. The game used the same graphics settings as the previous trial. [Captured frame](window-depth.jpg) · [Complete frame log](window-depth-frames.csv) · [JSON results](window-depth-summary.json)

| Accepted frames | Median | P95 | Longest | Frames over 200 ms |
| ---: | ---: | ---: | ---: | ---: |
| 268 | 336.9 ms | 376.3 ms | 410.2 ms | 268 |

The window was visible by 514.5 seconds on the renderer clock. The measurement plan allowed two minutes of warm-up and selected seconds 640–730 in advance. Mean workload was 4,869 draws per frame. Across 16 diagnostic log intervals the median cost attributed to buffer copy-back was 189.1 ms, compared with 11.3 ms for preparing textures. These timings cover overlapping operations and should not be summed. The median count of pipelines still compiling was zero. Shader `f133e35efed2a48a` still failed translation on this build. An independent RTX 4090 test associates the same sunlit shoulder defect with this and other missing compute programs. [Upstream comparison](https://github.com/fxceless/victory-fork/issues/62#issuecomment-7175666292)

Квадратный контур остался и после правки стекла. Все 268 принятых кадров в прогретом отрезке заняли больше 200 мс. По данным этого запуска обратное копирование буферов заслуживает отдельного теста производительности.

A glass pane behind a character can overwrite depth and motion for pixels that should have failed the depth test. That makes the window a useful place to test the square fringe. Upstream PR 907 added the Xbox early depth/stencil flag to eligible translated pixel shaders and reported that it removed a glass artifact on an RTX 5070 Ti. The RTX 3090 trial includes that patch. [Upstream implementation and authorship](https://github.com/fxceless/victory-fork/pull/907)

The local GPU change also filters a new write declaration against overlapping pending ranges before the emulator snapshots buffer memory. It returns immediately when an existing declaration covers the target. The coverage fixture compares the results byte for byte with a reference map. This adapts the single-pass subtraction approach discussed in PR 1159. Both the coverage fixture and the early-depth translation fixture passed in the optimized Windows diagnostics build. [Upstream range work](https://github.com/fxceless/victory-fork/pull/1159)

## Reproduce

1. Apply the two patches in the [lighting-trial guide](lighting-trial.md) to upstream revision `9376fd60c0ba0e76a74c39b49b1407dbac0a64c7`.
2. Apply the [window-depth patch](../../patches/victory-rtx3090-window-depth.patch) next. Build using the commands below.
3. Use the same Series X profile and a copy of the same save. Start a new shader and pipeline cache for this translator. The measured run reused only the list of pipeline priorities. The graphics settings file was byte-identical across the reference and both trial runs.
4. Pass `VICTORY_FRAME_CSV` as an absolute path to a new file, `VICTORY_CARD_REHASH_RUNS=1`, `VICTORY_BLACK_FRAME_PROBE=0`, `VICTORY_MEMORY_MAP=0` and `VICTORY_LOG=warn,victory_gpu::host=info` to the renderer process. The black-frame probe is the optional readback used to diagnose blank frames. This option preserves the game's own render passes. The new counter requires DXGI to return S_OK, so occluded presents do not count toward FPS.

```powershell
cargo test --locked --profile diag --features diagnostics -p victory-gpu --lib clipped_snapshot_gaps_match_a_byte_map
cargo test --locked --profile diag --features diagnostics -p victory-shader --lib a_pixel_program_tested_before_it_runs_declares_early_depth
cargo build --locked --profile diag --features diagnostics -p victory
```

The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for the local snapshot change, integration and measurements. The shader change belongs to the upstream contributors.
