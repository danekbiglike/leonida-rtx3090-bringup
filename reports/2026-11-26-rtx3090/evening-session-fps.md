# Evening frame-rate check on the RTX 3090

The local Series X session on November 26, 2026 recorded 31,871 frame intervals over 117.49 minutes. After the first ten minutes, zero of 107 complete minutes averaged 5 FPS. The fastest minute averaged 4.55 FPS.

In 102 of those minutes every overlapping frame reported at least 1,000 draws. The median of the per-minute frame rates in that subset was 3.55 FPS, with a range of 1.92 to 4.55 FPS. Draw count alone cannot identify a scene or show whether a player was moving.

The runtime log identifies the Series X profile. This recording has no route markers or synchronized input record, and its renderer revision is unverified. It gives an observed frame-rate range for a long session. For the measured escort route, see the [separate controlled run](bitsets-only-escort.md).

[Per-minute counts](evening-session-minutes.csv) cover each complete, non-overlapping 60-second window of accumulated present intervals. Each frame counts in the window where its interval ends (a frame ending exactly on a minute boundary counts in the preceding minute). The minimum draw count includes every interval overlapping the window. FPS equals presents divided by 60. The final partial minute is omitted. The original frame timing CSV has SHA-256 `d0e11331e44bc55ec195ecf461f5d111becbb638505ce63b7d9871a24059208d`.
