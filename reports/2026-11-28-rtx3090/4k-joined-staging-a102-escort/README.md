# Joining staging reads up to 4 KiB apart on the RTX 3090

Both walks start at the A-102 sign and end in the dayroom, with Series X settings, 3840 × 2160 output and no frame generation or DLSS. Allowing GPU reads from the same input buffer to span gaps up to 4 KiB produced 2,072 presentations in 120 seconds, **17.27 FPS**. The same executable with zero gap recorded 2,154 presentations, **17.95 FPS**. Dark figures persisted by the dayroom bars in both runs. [Gate and dayroom side by side](compared-endpoints.jpg) · [Control](../4k-compact-staging-a102-escort)

| Staging join gap | Mean FPS | Worst five seconds | 95th-percentile frame time | Longest frame |
| --- | ---: | ---: | ---: | ---: |
| 0 bytes | 17.95 | 11.8 FPS | 77.69 ms | 337.76 ms |
| 4 KiB | 17.27 | 12.0 FPS | 85.61 ms | 162.76 ms |

Across 115 complete telemetry windows on each escort, the median window reported 688 staging reads for 5,244 fills per frame with zero gap and 701 reads for 5,384 fills with a 4 KiB gap. The frame workloads varied between walks. The CPU submission thread consumed 39.20 and 38.85 ms of CPU time per presentation respectively. The larger gap produced no gain in average FPS on this route. Neither walk reached 25 FPS in any five-second interval. [GPU copy counters](card-fills.csv) · [CPU samples](thread-cpu.csv) · [Frame times](escort-frames.csv)

Both runs used renderer SHA-256 `4bdcc470c0048ba7a4fd520b7e856f69066df8f910426331e001a62d78205d24`. The joined route finished with at least 4.09 GiB physical memory available. [Route metrics](escort-metrics.json) · [Hardware copy checks](../d3d12-staging-copy-capacity-fallback) · [Upstream change](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/1137)
