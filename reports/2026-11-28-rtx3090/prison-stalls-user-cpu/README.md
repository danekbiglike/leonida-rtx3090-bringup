# CPU activity inside two long prison frames on the RTX 3090

During the 10.094-second pause while turning the camera toward the common room, the busiest renderer thread consumed 8.266 CPU seconds in 8.289 seconds of sampling. The entire process spent only 1.031 CPU seconds in kernel mode over a slightly longer surrounding interval. This gives an estimated minimum of **7.23 CPU seconds in user mode for that single thread**. The corresponding estimate at the cell gate was **10.45 CPU seconds** during a separate 13.257-second pause. These frames ran with native Series X settings and 4K output on a Ryzen 7 3700X. [Camera samples](camera.json) · [Gate samples](gate.json)

| Frame | Process observation | All threads, kernel CPU | Busiest thread, CPU | Estimated minimum user CPU on that thread |
|---|---:|---:|---:|---:|
| Camera turn | 9.004 s | 1.031 s | 8.266 s | 7.234 s |
| Gate | 13.005 s | 1.906 s | 12.359 s | 10.453 s |

Windows sampled the renderer process and its individual threads on separate clocks. We used only process samples inside the frame and only complete thread intervals inside the process window. Subtracting the entire process's kernel time from the busiest thread's total gives a conservative estimate, subject to Windows scheduling-accounting granularity and the time spent collecting each sample. Process CPU seconds can exceed elapsed seconds when multiple threads run. The data cannot identify the function running on that thread or distinguish useful computation from busy waiting.

The accompanying sampler now records user and kernel CPU separately for each observed thread. The two estimates above use archived recordings from the earlier total-only sampler. [Analysis script](analyze.py) · [Updated Windows sampler](thread_cpu.cpp) · [Original camera recording](../4k-gate-and-xor-row-copy) · [Original gate recording](../4k-cpu-preparation-and-face-buffer-trial)
