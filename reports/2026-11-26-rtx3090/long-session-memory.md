# Four-hour continuation on the RTX 3090

The same renderer process that walked the [prison escort](heap-owner-escort.md) was still presenting after 4 hours 20 minutes. The Windows launcher sampled it 15,592 times through that cutoff. Its peak process commitment reached **34.67 GiB** with a 42 GiB cap. The first sample above the previous 34 GiB cap was at **258.6 minutes**. Windows reported no process-limit event during this interval. The smallest system commit headroom was 6.09 GiB. The longest gap between memory samples was 1016 ms.

Only the three one-minute samples in the linked escort report had a recorded route. This continuation measures process lifetime and memory under that run's varying workload. It does not establish four hours of active play, a lower memory footprint than the previous renderer, or a frame-rate gain.

[One-second Windows counters](heap-owner/long-session-memory.csv). To reproduce the figures from the repository root:

```powershell
python tools/summarize_memory_capture.py reports/2026-11-26-rtx3090/heap-owner/long-session-memory.csv --old-cap-gib 34
```
