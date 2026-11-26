"""Summarize a Windows launcher memory.csv and compare with a previous process cap."""
import argparse
import csv
import json
from pathlib import Path

GIB = 1024 ** 3


def summarize(path, old_cap_gib):
    if old_cap_gib <= 0:
        raise ValueError("The previous cap must be positive")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        samples = [{key: int(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    if not samples:
        raise ValueError("No memory samples")
    if any(a["uptime_ms"] >= b["uptime_ms"] for a, b in zip(samples, samples[1:])):
        raise ValueError("Sample times must increase")
    peak = max(row["job_peak_bytes"] for row in samples)
    crossing = next((row for row in samples if row["job_peak_bytes"] > old_cap_gib * GIB), None)

    def headroom(row):
        return row["system_commit_limit_bytes"] - row["system_commit_bytes"]

    return {
        "samples": len(samples),
        "last_uptime_seconds": samples[-1]["uptime_ms"] / 1000,
        "process_limit_gib": samples[-1]["process_limit_bytes"] / GIB,
        "process_peak_commit_gib": peak / GIB,
        "max_polled_private_gib": max(row["private_bytes"] for row in samples) / GIB,
        "min_free_system_commit_gib": min(map(headroom, samples)) / GIB,
        "min_physical_available_gib": min(row["physical_available_bytes"] for row in samples) / GIB,
        "previous_cap_gib": old_cap_gib,
        "first_sample_above_previous_cap_s": crossing["uptime_ms"] / 1000 if crossing else None,
        "system_commit_headroom_at_crossing_gib": headroom(crossing) / GIB if crossing else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--old-cap-gib", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.csv, args.old_cap_gib), indent=2))
