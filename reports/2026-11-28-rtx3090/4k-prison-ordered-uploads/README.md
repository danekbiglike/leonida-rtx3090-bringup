# RTX 3090 at gate A-102 and the interview after the buffer ordering fix

Lucia reached the counselor's desk on this run. The first saved view of both characters at the desk came **204.36 seconds** after the gate marker. Across that interval the renderer presented **3,572 frames, averaging 17.48 FPS**. The longest interval was 228.3 ms. The last 15 seconds included camera input and screenshots. The exact instant the interview began falls between captures. [Desk capture](interview-desk.jpg) · [Camera sequence](camera.jpg) · [Gate-to-desk frames](gate-to-desk-frames.csv) · [Interval summary](gate-to-desk.json)

## The repeatable 120-second test

The RTX 3090 presented **2,088 frames, averaging 17.40 FPS** in the first two minutes from the officer at A-102. The slowest five seconds averaged **13.6 FPS**, the fastest **19.4**. Neither minute nor any of the 24 five-second windows reached 25 FPS. The 95th-percentile frame interval was 78.1 ms and the longest was 149.1 ms. [Route](escort-route.jpg) · [Frame times](escort-frames.csv) · [Metrics](escort-metrics.json)

The previous worker-copy trial began beside the same door and ended in a similar view of silhouetted figures. It averaged 16.89 FPS with 13.8 FPS in the slowest five seconds. The current run combines the older worker configuration with the buffer ordering fix. Scene timing and camera angles also differ slightly. The 0.51 FPS difference cannot be attributed to the patch alone. The earlier row-copy trial reached the seated interview inside the 120-second window. [Paired endpoint images](compared-endpoints.jpg) · [Worker-copy trial](../4k-gate-buffer-copy-worker) · [Row-copy trial](../4k-row-copy-gate-to-interview)

## Lighting and the cell

The silhouetted room was still dark at 120 seconds. At 189.7 seconds Lucia was standing by the next door. Her face was visible in the subsequent camera views and the doorway was strongly overexposed in one. The interview captures show the counselor, desk, shelves and lamp. Camera position and lighting differ from the earlier facial-shadow screenshots. This run provides no evidence that the intermittent square highlights have been fixed. [At the next door](post-escort.jpg) · [Camera sequence](camera.jpg) · [Stationary cell samples](stationary-cell.jpg)

The separately measured 120 seconds beginning in the cell contained 1,424 frames, averaging **11.87 FPS**. The worst five seconds averaged **5.6 FPS**. One frame took **1.40 seconds**. The last image shows Lucia in the corridor. [Cell route](cell-route.jpg) · [Cell metrics](cell-metrics.json) · [Long frame details](long-frames.json)

## Configuration and remaining costs

Series X settings, 3840 × 2160 output, RTX 3090, Ryzen 7 3700X, SSD. DLSS and frame generation were off. The run used the same approximate indirect lighting and reflection settings as the row-copy trial. GPU utilization had a 96% median during the gate test. Available physical RAM stayed above 4.40 GiB. The renderer closed after capture. SHA-256 was `03e93a2f93a89cb079c2bb663ec01eb9a1d2948a0039cb234c1d09a62e3bfbe6`. [GPU samples](escort-gpu.csv) · [Omitted draws](escort-pipelines.csv)

The median of the per-frame submission reports was 53.2 ms, including 6.5 ms checking for writes. The GPU queue reported a median 14.9 ms per frame idle behind the submitting thread. Complete pairs of resource-residency counter samples within the gate window recorded 12,000 waits totaling 10.62 seconds. A separate counter for mapping recorded 8,000 waits totaling 7.36 seconds. The counters cover different operations and portions of the window and cannot be added as a frame-time saving. They do not identify the allocation type. [Submission samples](escort-submission.csv) · [Residency sample intervals](phase-residency.csv) · [Paging estimates](escort-paging.json)

The independent GPU readback tests and the upstream change are available separately. [RTX 3090 byte comparisons](../rtx3090-deferred-copy-ordering) · [VIctory-NVIDIA PR 874](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/874)
