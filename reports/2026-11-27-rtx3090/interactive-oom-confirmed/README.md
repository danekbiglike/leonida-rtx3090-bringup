# Memory exhaustion in the interactive RTX 3090 session

The integrated Series X renderer ran from the SSD with ordinary texture uploads. At 824.453 seconds after launch its Windows job delivered message 9, the per-process memory-limit notification. The recorded peak was 44,624,150,528 bytes against a 44,624,371,712-byte limit. Only 216 KiB separated them. The nearest system sample had 883 MiB of commit headroom. The renderer's terminal log reported failed allocations of 512 KiB and 2 MiB. The memory sampler continued to run after rendering stopped. Its last timestamp is not a gameplay-duration measurement. [Measurements](metrics.json) · [Selected samples](memory.csv) · [Windows notification semantics](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port)

During the final texture report, 824.1 of 828.5 ms per frame across the texture workers were spent waiting for memory remapping. These are accumulated worker times and can overlap. The job event establishes that an allocation reached the process limit. It does not identify which subsystem retained the bytes. It also shows why the process and system budgets both matter in long-session tests.

Measurement ID `danekbiglike/rtx3090-20261127-interactive-oom`. Local measurement on Ryzen 7 3700X and RTX 3090 by the danekbiglike bring-up project with ChatGPT.
