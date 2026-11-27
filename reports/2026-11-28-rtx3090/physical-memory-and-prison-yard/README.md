# Three 4K startup runs on the 32 GiB Ryzen and RTX 3090 PC

The tuned renderer with all eight compute pipelines reached the prison yard. Bright gradients had visible bands and the character's hair showed block-shaped gaps. At the end of the run the last successful frame preceded the guest watchdog failure by roughly a minute. The escort could not be measured. The faster in-game comparison on this machine remains the earlier 10.02 FPS corridor run, which also has reported visual defects. [Yard capture](yard.jpg) · [Eight-pipeline validation](../eight-compute-pipelines-on-ssd-renderer/) · [Measured corridor](../../2026-11-27-rtx3090/stable-player-corridor-boundary-captures/)

| Renderer | Runtime | Lowest available physical RAM | Peak working set | Outcome |
|---|---:|---:|---:|---|
| Tuned SSD | 182 s | 2.08 GiB | 20.17 GiB | The monitor stopped its job after eight low-memory samples |
| Tuned SSD with batched constant descriptors | 586 s | 3.28 GiB | 15.93 GiB | Reached the yard and exited at guest offset +0x23cf683 |
| NVIDIA paired-wave candidate | 171 s | 5.69 GiB | 16.47 GiB | Exited during loading at the same offset |

For the second run Windows confirmed a process working-set ceiling of 17,103,683,584 bytes at startup. The renderer retained up to 31.23 GiB of private commitment. The physical-memory stop conditions stayed enabled throughout. The first two runs also differed in cache warmth and CPU-side descriptor code, so their duration cannot establish the effect of the ceiling alone. The NVIDIA run followed a separate two-worker preload that placed 1,200 recorded pipelines into its library in 746 s. This did not get that build through loading.

All three runs used the same cloned Series X settings and 3840 × 2160 output. Each used temporary access to SSD game data and wrote to an isolated trial directory. Renderer hashes and raw byte counts are included. [Summary](summary.csv) · [Tuned renderer](stable-tuned-memory.csv) · [Working-set ceiling](stable-slots-memory.csv) · [NVIDIA renderer](nvidia-paired-memory.csv) · [Windows working-set API](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-setprocessworkingsetsizeex)
