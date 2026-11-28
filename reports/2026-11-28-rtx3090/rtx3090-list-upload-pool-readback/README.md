# RTX 3090 command-list upload reuse

On this Ryzen 7 3700X and RTX 3090, obtaining an 8 MiB shared buffer took a mean **983.8 µs** when allocated for each request and **4.3 µs** when the previous list's retired buffer could be reused. Our GPU readback probe verified every byte from nine list uploads both with recycling enabled and disabled. With recycling enabled, six of the nine buffers were reused. [Allocation timings](times.csv) · [Byte checks](readback.csv)

| Shared buffer | Mean, fresh | Mean, recycled | Fresh p99 |
| --- | ---: | ---: | ---: |
| 64 KiB | 336.5 µs | 1.7 µs | 489 µs |
| 1 MiB | 352.7 µs | 1.8 µs | 808 µs |
| 8 MiB | 983.8 µs | 4.3 µs | 1,686 µs |

The upstream allocation test made 200 requests for each size, allocation type and policy. Timing uses whole microseconds. Most recycled hits finished below its reporting resolution. Recycled means include the first allocation. The tests ran with the game closed and without an artificial background allocation load. The live renderer has other allocation types and can hold several buffers in flight. A per-request saving does not establish a corresponding increase in game FPS. [Implementation and original test by 0xkn0wh3r3](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/923)

## Checking data lifetime

Three recorded lists each copy a different 65,537-byte payload to a separate region of a mapped output buffer. The GPU queue waits on a fence until all three submissions return. After completion, the CPU checks every expected byte and the 15 padding bytes after each region. The lists then retire and the sequence runs twice more with different patterns. Both modes preserved all payloads and all 135 checked guard bytes. The three independent deferred-upload probes also passed on the pooled build. [Readback test patch](gpu-readback.patch) · [Earlier deferred-upload probes](../rtx3090-deferred-copy-ordering)

The new probe applies to the previously measured ordered-upload source with PR 923's pool functions. With the native D3D12 hardware selected, run `three_list_uploads_keep_their_data_across_pool_reuse` as an ignored victory-gpu library test in a fresh process for each value of `VICTORY_UPLOAD_POOL` (0 and 1). The tests used `VICTORY_RELAY=2`, `VICTORY_RELAY_COPY=1`, `VICTORY_CARD_ALL=0` and `VICTORY_COPIES_IN_PLACE=1`.
