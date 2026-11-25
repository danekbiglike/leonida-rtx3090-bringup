# Investigating square lighting artifacts on the RTX 3090

The reference scene is the prison window and adjoining room in gameplay. The reported fault is a bright, square-edged fringe on the character or wall that can come and go with the light and camera. Multicolored skin, missing indirect light and a temporary blur in the flashback are separate observations.

## Changes under test

| Source | Change in the trial | What it tests |
| --- | --- | --- |
| [fxceless/victory-fork PR 834](https://github.com/fxceless/victory-fork/pull/834) | Port a second indirect dispatch and its group-ID offset to the older pinned renderer. This trial limits the extra dispatch to single-record commands. | The classified-tile lighting shader can request more than 65,535 groups in X. The missing work can leave tiles with values from an earlier shot. |
| [fxceless/victory-fork PR 823](https://github.com/fxceless/victory-fork/pull/823) | Use the upstream list of eligible 32-lane shader translations and group contiguous page aliases. | A previously refused reflection classification shader can leave a stale tile list. |
| [fxceless/victory-fork PR 1031](https://github.com/fxceless/victory-fork/pull/1031) | Bound texture queue selection while preserving its chosen slots and their order. | Reduces CPU sorting work in a streaming backlog. |
| This repo | Record one interval per present, add same-process controls and a frame-time summary tool. | Separate changes in pacing from changes in the scene. |

The pinned PR heads are `b9ab1ee0fbc7e66a60322f60f768aeb43e3e23e3`, `aaf658a40f3e512550165e489a0f0c411e3c9544` and `db88f96a6c940b33671c613eecf44c76f06a902b`, respectively. Additional reports reproduced the mosaic with shader optimization disabled. [Correction and follow-up](https://github.com/fxceless/victory-fork/issues/310#issuecomment-7152252422)

## Reproduce

Apply the streaming patch from the [base report](README.md) to revision `9376fd60c0ba0e76a74c39b49b1407dbac0a64c7` and then apply the [lighting trial patch](../../patches/victory-rtx3090-lighting-trial.patch). Use the same build command. Use separate writable cache and save directories for this trial and start with an empty shader cache. Pass an absolute new file path in `VICTORY_FRAME_CSV` to the renderer. Set `VICTORY_CARD_REHASH_RUNS=1` to group touching hash ranges. Leave the graphics profile and resolution as in the base run.

While the renderer is open, creating an empty `split-off` beside the CSV disables the overflow pass. Removing that file enables it. A `rehash-off` file controls the grouped hash passes in the same way if the environment option is enabled. The renderer checks the files about once per second. The CSV records which modes were active. Let work already in flight finish before comparing screenshots.

The Direct3D WARP fixture `warp_split_runs_every_group_of_a_wide_dispatch_once` verifies that the overflow pass executes exactly once for every requested group in its supported range and checks the work budget. The texture-queue order and joined-piece coverage fixtures also passed locally.

Record the start time of a **controllable** scene before measuring and keep the complete interval, including stalls. Window-caption FPS, menus, loading and cutscenes do not establish stable gameplay. Run the summary tool on the resulting CSV, replacing the example start time with the observed gameplay start.

```powershell
python tools/summarize_gameplay.py frame-times.csv --start 300 --seconds 90
```

For a strict 5 FPS floor every included present interval must take at most 200 ms. The clock measures application presents. The tool reports P50, P95, P99, the longest interval and the number over 200 ms. [Summary tool](../../tools/summarize_gameplay.py)

## Measured prison gameplay

The renderer reached the prison window and showed the movement tutorial. The same position and camera were held across four predetermined 90-second windows. Only idle animation, scene streaming and the listed switches varied. The first window includes warm-up after player control became available. The paired lighting dispatch ran on this RTX 3090. Square stair steps on Lucia’s sunlit shoulder remained visible with the dispatch enabled and disabled.

| Window | Start (s) | Split lighting | Joined hashes | FPS | P95 (ms) | Longest (ms) | Frames over 200 ms / total |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| A | 615 | on | on | 1.90 | 1183.9 | 1362.0 | 171 / 171 |
| B | 725 | off | on | 2.98 | 369.3 | 497.5 | 268 / 268 |
| C | 837 | on | off | 3.02 | 366.4 | 413.9 | 273 / 273 |
| D | 947 | on | on | 2.93 | 373.4 | 717.0 | 265 / 265 |

The CSV includes the entire session from startup through the last measured interval. Times refer to calls to Present in the emulator. This build did not record the DXGI status or physical scanout. All four intervals missed the 5 FPS floor. The order and progressive warm-up limit attribution of small differences to either switch. [Raw per-frame CSV](prison-window-frames.csv) · [Machine-readable results](prison-window-summary.json)

## Кратко по-русски

RTX 3090 и Ryzen 7 3700X. У тюремного окна после прогрева получилось около 3 FPS. В каждом из четырёх заранее выбранных отрезков были кадры дольше 200 мс. На контуре плеча Люсии при переключении исправления остаются квадратные ступеньки. Исходники и тесты доступны выше.

Upstream shader, dispatch and queue contributions are credited in the table above. The project owner credits ChatGPT Astra 6.2 at very high reasoning effort for the local integration, instrumentation and RTX 3090 report.

Both screenshots show the prison window with grouped hashes enabled. Look at the sunlit edge of Lucia’s right shoulder. The two captures show different phases of her idle animation. The FPS in the title bars is a short sample. [Split lighting off](window-split-off.jpg) · [Split lighting on](window-split-on.jpg) · [Follow-up on glass and depth](window-depth.md)
