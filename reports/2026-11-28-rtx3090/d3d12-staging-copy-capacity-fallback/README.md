# Preserving GPU buffer copies when coalescing exceeds 4 MiB

On our RTX 3090, D3D12 produced the expected destination bytes for all three tested staging layouts. Forty nearby 256-byte reads could share one copy into the staging buffer. For 1,200 sparse reads, the local fallback kept the batch within the 4 MiB buffer and preserved all destination bytes. The test checked the sentinel bytes in every destination gap and the device message log after queue completion. [Hardware test output](hardware-test.txt)

| Logical reads | Source stride | Allowed gap | Copies into staging | Staging bytes occupied |
| ---: | ---: | ---: | ---: | ---: |
| 40 | 512 B | 0 B | 40 | 10,240 |
| 40 | 512 B | 4,096 B | 1 | 20,224 |
| 1,200 | 4,096 B | 4,096 B | 1,200 | 307,200 |

Foxhound's [PR 1137](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/1137) groups nearby reads from the same backing buffer and dependency level. Its 4 KiB gap setting would make the third case a single 4,911,360-byte span, exceeding the intermediate buffer. The local change retries that batch with individual reads; a batch too large even after compaction still follows the renderer's existing refusal path. The patch applies to upstream revision `b5ea86d837f980500205dc66287c0243369b68f1`. [Patch and native test](preserve-staging-capacity.patch)

All eight CPU layout tests passed, including alignment, overlapping and duplicated ranges, the exact capacity boundary, and a buffer one byte too small. The standalone test and the native D3D12 test use generated inputs. These results establish copy correctness; measuring gameplay throughput requires a separate timed prison route on each setting. [CPU test output](layout-tests.txt)
