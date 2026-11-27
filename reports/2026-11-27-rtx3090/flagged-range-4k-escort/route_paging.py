"""Align the five longest present gaps with the renderer and volume counters."""

import csv
import json
from pathlib import Path
import sys


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def weighted(start, end, samples):
    covered = total = 0.0
    for low, high, value in samples:
        overlap = max(0.0, min(high, end) - max(low, start))
        covered += overlap
        total += overlap * value
    return round(covered / (end - start), 3), round(total, 3)


def export(trace, report):
    start = int((trace / "walk-start.txt").read_text()) / 1000
    frames = read(report / "frames.csv")
    faults = read(trace / "process-faults.csv")
    counters = read(trace / "disk-faults.csv")
    process = []
    for first, last in zip(faults, faults[1:]):
        a, b = (int(row["utc_us"]) / 1e6 for row in (first, last))
        process.append((a, b, (int(last["hard_faults"]) - int(first["hard_faults"])) / (b - a)))
    disks = {}
    for key in ("game_disk_read_bytes_s", "cache_volume_read_bytes_s",
                "cache_volume_write_bytes_s", "paging_disk_read_bytes_s"):
        disks[key] = [(float(a["utc_s"]), float(b["utc_s"]), float(b[key]) / 2**20)
                      for a, b in zip(counters, counters[1:]) if b[key]]
    gaps = []
    for f in sorted(frames, key=lambda r: -int(r["present_interval_us"]))[:5]:
        end = start + int(f["elapsed_us"]) / 1e6
        seconds = int(f["present_interval_us"]) / 1e6
        begin = end - seconds
        coverage, count = weighted(begin, end, process)
        values = dict(end_offset_s=round(end - start, 3), interval_s=seconds,
                      process_coverage=coverage, estimated_process_hard_faults=count)
        for key, samples in disks.items():
            coverage, mib = weighted(begin, end, samples)
            values[key.removesuffix("_bytes_s") + "_mib"] = mib
            values[key.removesuffix("_bytes_s") + "_coverage"] = coverage
        gaps.append(values)
    result = {"report_id": frames[0]["report_id"], "longest_gaps": gaps}
    (report / "paging.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(gaps[0]))


if __name__ == "__main__":
    export(Path(sys.argv[1]), Path(sys.argv[2]))
