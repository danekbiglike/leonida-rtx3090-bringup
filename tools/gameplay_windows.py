"""Count accepted presents in nonoverlapping windows of a VIctory frame CSV."""
import argparse
import csv
import json
from pathlib import Path


def count_windows(path, start, seconds, window=5):
    if start < 0 or seconds <= 0 or window <= 0 or seconds % window:
        raise ValueError("Use a nonnegative start and a positive duration divisible by the window size")
    start_us = start * 1_000_000
    stop_us = (start + seconds) * 1_000_000
    window_us = window * 1_000_000
    counts = [0] * (seconds // window)
    elapsed = 0
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            interval = int(row["present_interval_us"])
            if interval <= 0:
                raise ValueError("Nonpositive present interval")
            elapsed += interval
            if start_us < elapsed <= stop_us:
                counts[(elapsed - start_us - 1) // window_us] += 1
            if elapsed >= stop_us:
                break
    if elapsed < stop_us:
        raise ValueError("Capture ends before the last window")
    return {
        "start_seconds": start, "stop_seconds": start + seconds, "bin_seconds": window,
        "accepted_presents": counts, "minimum_fps": min(counts) / window,
        "bins_at_least_5_fps": sum(n >= 5 * window for n in counts),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--seconds", type=int, required=True)
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(count_windows(args.csv, args.start, args.seconds, args.window), indent=2))
