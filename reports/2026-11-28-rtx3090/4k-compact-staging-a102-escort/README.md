# Compact GPU staging on the RTX 3090 prison escort

Lucia followed the officer from A-102 to the dayroom. The renderer presented **2,154 frames in 120 seconds (17.95 FPS)** at Series X settings and 3840 × 2160 output. This is the highest mean among our camera-verified 4K escort runs so far. The worst five-second interval was 11.8 FPS, the best was 20.6, and none of the 24 intervals reached 25 FPS. The 95th-percentile frame time was 77.69 ms, the longest was 337.76 ms, and at least 3.67 GiB of physical RAM was available during the walk. The dark figures near the dayroom bars remained visible. [Gate and endpoint comparison](compared-endpoints.jpg) · [Frame times](escort-frames.csv) · [Metrics](escort-metrics.json)

| 4K escort | Mean FPS | Worst five seconds (FPS) | 95th-percentile frame time |
| --- | ---: | ---: | ---: |
| This run, 0 B staging join gap | 17.95 | 11.8 | 77.69 ms |
| [Depth audit](../4k-prison-depth-and-write-audit) | 17.62 | 12.4 | 75.93 ms |
| [Temporary-buffer read slots](../4k-temporary-buffer-read-slots-escort) | 17.46 | 14.0 | 80.60 ms |

The measured setting used one staging copy for each distinct input record. All 115 complete reporting windows inside the escort logged a zero gap. The median window reported 688 staging reads and 5,244 fills per frame. This is the zero-gap control for the [joined-copy experiment](../4k-joined-staging-prison-cell). The 4 KiB run reached the same room but missed the gate timing marker. Its figures cannot establish an escort FPS difference between the two settings. One walk also cannot resolve a 0.33 FPS average difference from the previous best. [GPU copy counters](card-fills.csv)

The separately timed cell interval presented 1,537 frames (12.81 FPS), with five-second averages from 9.0 to 17.4 FPS. By the end of that interval the control camera was already in the corridor behind the officer. The 4 KiB run ended its cell interval beside the bunks. The 13.36 and 12.81 FPS cell averages therefore cover different views. Both settings used the same executable, SHA-256 `4bdcc470c0048ba7a4fd520b7e856f69066df8f910426331e001a62d78205d24`, full GPU write declarations, no frame generation and no DLSS. [Cell images](cell-route.jpg) · [Cell metrics](cell-metrics.json) · [Escort GPU samples](escort-gpu.csv)
