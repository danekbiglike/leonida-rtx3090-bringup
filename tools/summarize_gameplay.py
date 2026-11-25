"""Summarize a predetermined gameplay segment of VIctory's frame CSV."""

import argparse
import csv
import json
import math
from pathlib import Path


def summarize(path, start, seconds):
    if start < 0 or seconds <= 0 or not all(map(math.isfinite, [start, seconds])):
        raise ValueError("start must be nonnegative and duration positive")
    first = round(start * 1_000_000)
    end = first + round(seconds * 1_000_000)
    elapsed = 0
    frame_times = []
    draws = []
    split_modes = set()
    hash_modes = set()
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            duration = int(row["present_interval_us"])
            if duration <= 0:
                raise ValueError("invalid present interval")
            begin = elapsed
            elapsed += duration
            if begin >= end:
                break
            if elapsed > first:
                # Keep frames crossing either edge intact, including long stalls.
                frame_times.append(duration)
                draws.append(int(row["draw_calls"]))
                if "split_enabled" in row:
                    split_modes.add(int(row["split_enabled"]))
                if "joined_hashes" in row:
                    hash_modes.add(int(row["joined_hashes"]))
    if elapsed < end or not frame_times:
        raise ValueError("the capture does not cover the requested interval")
    ordered = sorted(frame_times)
    def percentile(p):
        return ordered[math.ceil(len(ordered) * p) - 1] / 1000
    return {
        "start_seconds": start, "requested_seconds": seconds,
        "covered_seconds": sum(frame_times) / 1_000_000,
        "frames": len(ordered), "fps": 1_000_000 * len(ordered) / sum(ordered),
        "p50_ms": percentile(.50), "p95_ms": percentile(.95),
        "p99_ms": percentile(.99), "max_ms": ordered[-1] / 1000,
        "frames_over_200ms": sum(t > 200_000 for t in ordered),
        "all_frames_within_200ms": ordered[-1] <= 200_000,
        "mean_draw_calls": sum(draws) / len(draws),
        "split_modes": sorted(split_modes), "joined_hash_modes": sorted(hash_modes),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--start", type=float, required=True, help="seconds into the capture")
    parser.add_argument("--seconds", type=float, default=90)
    args = parser.parse_args()
    print(json.dumps(summarize(args.csv, args.start, args.seconds), indent=2))
