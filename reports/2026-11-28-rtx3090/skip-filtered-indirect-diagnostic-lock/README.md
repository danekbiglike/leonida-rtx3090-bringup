# Avoiding the indirect-signature logging lock when its message is disabled

On three camera-verified 4K prison escorts, the renderer reported median rates of **626, 633 and 626 dropped indirect executions per frame**. Each increments a counter and then locks a shared table used solely to print the first diagnostic for each command signature. Our gameplay log filter suppresses that module's informational messages. Checking whether the event is enabled before looking up the signature removes a lock acquisition for every such drop while preserving the counter. The patch changes no GPU commands, shaders or image settings. [Renderer patch](guard-first-use-log.patch)

| 120-second escort | Complete log windows | Median indirect drops/frame | Windows reporting zero pipelines being compiled |
| --- | ---: | ---: | ---: |
| [Depth audit](nvidia-depth-audit.csv) | 23 | 626 | 18 |
| [Temporary-buffer read slots](nvidia-depth-fill-slots.csv) | 23 | 633 | 23 |
| [Wave32 meshlet collection](nvidia-depth-wave822.csv) | 22 | 626 | 22 |

The test used the patched Rust code and tracing libraries from the renderer build. Eight concurrent threads made 1,600 calls across two different command signatures. With the module filtered out, all 1,600 drops were counted without a single lock acquisition. With its informational logging enabled, the counter also reached 1,600 and exactly two messages were emitted. The filtered signatures stay unrecorded until their diagnostics are enabled. The test instruments lock attempts, without measuring elapsed time. The effect on gameplay FPS requires a timed run. [Test output](logging-check.json) · [Test fixture](check.py)

To extract the CSVs, run the analysis with a completed trial directory containing the gate marker and renderer log, followed by the output path. Each row is one full renderer reporting interval inside the 120-second route. Its pipeline lookup and drop counters are independently rounded per-frame rates; their difference is included for inspection. [Analysis script](phase_omissions.py)
