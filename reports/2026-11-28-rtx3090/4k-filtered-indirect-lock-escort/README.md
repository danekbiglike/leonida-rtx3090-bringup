# Indirect diagnostic lock on the 4K A-102 escort

Lucia followed the officer from A-102 into the dayroom. The RTX 3090 presented 2,034 frames in 120 seconds at 3840 × 2160 and Series X settings, with frame generation and DLSS off. Checking the log filter before taking the shared diagnostic lock gave **16.95 FPS** on this walk. The matching baseline recorded **17.62 FPS**. Neither the average nor the slowest five seconds improved in this pair. One walk per setting is insufficient to attribute a 0.67 FPS difference to the patch. [Frame times](escort-frames.csv) · [Gate and dayroom images](compared-endpoints.jpg)

| A-102 escort | Mean FPS | Worst five seconds | 95th-percentile frame time | Submit thread CPU time per present |
| --- | ---: | ---: | ---: | ---: |
| [Baseline](../4k-prison-depth-and-write-audit) | 17.62 | 12.4 FPS | 75.93 ms | 39.88 ms |
| Guarded diagnostic lookup | 16.95 | 12.0 FPS | 81.27 ms | 40.39 ms |

The guarded executable still recorded a median 626 dropped indirect command executions per frame over 23 complete reporting windows. This change only removes a lock used to log those drops. The [concurrent unit check](../skip-filtered-indirect-diagnostic-lock) verified that the drop counter still advances. Figures at the dayroom bars remained dark on both runs. No five-second interval reached 25 FPS. During the guarded walk the lowest available physical memory was 4.54 GiB and system commit headroom stayed above 17 GiB. The run ended with the requested test stop. [Metrics](escort-metrics.json) · [Pipeline counters](pipeline-counters.csv)

CPU time per present uses summed thread CPU time divided by summed presentations in the complete CPU sampling intervals. Those intervals cover 2,081 presentations in the baseline and 2,000 in the guarded run. The frame-rate measurements above use the whole 120 seconds. Executable SHA-256 for the guarded run was `9930824fe78620734eaa54a85e56a9ed8d62120c08d84e761a86af0620c42237`. [Baseline CPU samples](reference-thread-cpu.csv) · [Guarded CPU samples](thread-cpu.csv)
