# RTX 3090 escort with buffer bitsets and batched texture lookups

On the Ryzen 7 3700X and RTX 3090, the two-patch build reached the common area with the guard. Walking from the cell doorway along the corridor to gate A102 averaged **3.38 FPS**. From the gate further into the common area it averaged **2.17 FPS**. Both windows were 60 seconds of repeated forward input. None of their 24 five-second bins reached 5 FPS.

| Route | Frame count | P95 frame time | Longest frame | Slowest five seconds |
| --- | ---: | ---: | ---: | ---: |
| Doorway to A102 | 207 | 398 ms | 1,778 ms | 3.0 FPS |
| Through A102 | 131 | 779 ms | 2,912 ms | 1.0 FPS |

The previous heap-owner build averaged 3.08 FPS in its corridor sample and 2.44 entering the common room. The routes, timing of inputs and occupants differ between launches. Neither comparison isolates an FPS gain from the patches. The same save and settings were used. The Series X settings XML was byte-identical to the small-buffer profile (SHA-256 `558c63ca0073281e52487c52238be017ced26837d62e49f896f00acf537a4d22`). Hair banding and very dark people behind the gate are still visible. [Earlier escort and pictures](heap-owner-escort.md) · [Doorway](slot-bitsets/cell-door.jpg) · [A102](slot-bitsets/gate-a102.jpg) · [Inside the gate](slot-bitsets/behind-gate.jpg)

Median diagnostic intervals along the corridor spent 93 ms preparing buffer copies, 27 ms on textures, 100 ms waiting on the GPU and 92 ms copying back. Behind A102 the corresponding figures were 85, 88, 132 and 101 ms. These stages can overlap. [Renderer interval counters](slot-bitsets/escort-stages.csv)

## Paired live texture checks

Every sixteenth nonempty remap batch ran the original lookup and the sorted, combined lookup under the same lock, alternating which ran first. All **424** sampled batches returned exactly the same set of texture slots through the end of the second walk. In the **193** samples after a renderer interval reporting at least 500 draw calls per frame, the lookup totals were **67.20 ms original and 70.70 ms batched**. One sample accounts for a 6.58 ms swing. The measured route shows no aggregate saving from enabling this texture change. These times cover slot collection only and exclude the final sort and deduplication. The previous [synthetic bitset result](buffer-slot-bitsets.md) measures the separate buffer-descriptor change. [Per-batch times and equivalence](slot-bitsets/remap-samples.csv)

[Successful present intervals](slot-bitsets/gameplay-frames.csv) · [Exact starts, percentiles and five-second counts](slot-bitsets/escort-segments.json) · [Timed batches of actual W keypresses](slot-bitsets/escort-inputs.json). The first and last frame intervals are counted whole. To reproduce each mean, run `tools/summarize_gameplay.py` on the CSV with the corresponding JSON start and `--seconds 60`. The build, source and test procedure are in the [preceding report](buffer-slot-bitsets.md). Gameplay validation used `VICTORY_CHECK_REMAPS=1`.
