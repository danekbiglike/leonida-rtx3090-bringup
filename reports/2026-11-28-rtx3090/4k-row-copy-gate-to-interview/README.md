# RTX 3090 from gate A-102 to the interview with the faster texture copy

Lucia moved through the prison and reached the interview. In the 120 seconds beginning beside the officer at A-102, the RTX 3090 presented **2,017 game frames, averaging 16.81 FPS**. The two minutes averaged 17.15 and 16.47 FPS. The slowest five seconds averaged **2.6 FPS** and the fastest 21.6 FPS. The 95th-percentile interval was 84.8 ms. There were no five-second intervals at 25 FPS. The last capture shows Lucia seated at the desk. [Route captures](escort-route.jpg) · [Frame intervals](escort-frames.csv) · [Metrics](escort-metrics.json)

An earlier run from the open A-102 gate to the interview averaged 16.18 FPS, with 10 FPS in its slowest five seconds. Here the view started beside the officer facing the barred gate. The elapsed time spent walking and in cutscenes varied. The separate 18.96 FPS run finished at a closed gate. Comparisons across these runs cannot isolate the texture change. [Earlier interview](../4k-guard-escort-and-interview) · [Earlier closed gate](../4k-gate-and-xor-row-copy)

The cell interval started facing the bookshelf and ended with a close-up of the officer at B35. It contained 1,940 accepted presents in 120 seconds, averaging **16.17 FPS**, with 7.4 FPS in its slowest five seconds. An 11.27-second buffer update began about 0.87 seconds before this interval ended and finished afterward. The 606 ms maximum reported in the cell metrics covers frames whose terminating present fell within the window. [Cell captures](cell-route.jpg) · [Cell frames](cell-frames.csv) · [Cell metrics](cell-metrics.json)

## The four-second interview frame

One interval near the end of the escort lasted **4.092 seconds**. A watched-buffer refresh overlapped 4.033 seconds of it. The renderer asked which pages had changed in **111 µs**, then recorded **4.033 seconds** inside the copy routine while refreshing **192 KiB** from a requested 1,750,160-byte span. This timer includes waiting for locks and other workers. The two overlapping buffer timers describe the same operation. [Matched frame and events](long-frames.json) · [Refresh timings](slow-buffers.csv) · [Instrumentation patch](slow-buffer-timing.patch)

Windows registered no CPU-time increment on the instrumented worker, `victory-wide-2`, in the three complete sampling intervals inside the copy. Another renderer thread accumulated **3.078 CPU seconds over 3.095 seconds**, including 2.703 user-mode CPU seconds. The thread executing that work and the lock or operation the worker waited on are still unidentified. Rows with zero mean no increment was recorded by the per-thread sampler. [Three OS intervals](long-frame-cpu.csv)

## Image and settings

The interview sequence shows a sharp light-to-shadow boundary across Lucia's lower face in multiple views. Clothing, books, facial features and desk props are visible. The earlier moving square highlights cannot be judged from these captures. During the separate sequence of camera captures, the scene presented 284 frames in 14.442 seconds. The interview camera cut between speakers during this sequence. [Camera captures](camera.jpg)

Native Series X settings with 3840 × 2160 output, approximate indirect light and reflection limiting, DLSS and frame generation off. The GPU utilization median was 95% during the escort. Available physical RAM stayed above 4.60 GiB. The renderer closed on request at the end of the measured run. Renderer SHA-256 `66a7d1686cf76b3b3bcecb779d91ea57b336ccc37d590574712c61894c253d84`. [Escort GPU samples](escort-gpu.csv) · [Submission timings](escort-submission.csv) · [Omitted draws](escort-pipelines.csv) · [Byte-checked texture tests](../rtx3090-row-copy-gpu-roundtrip)
