"""Measure worker CPU time and concurrent preparation during a timed prison route."""
import argparse
import csv
import json
import re
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def measure(trial, marker):
    origin = int((trial / marker).read_text(encoding="ascii")) * 1000
    end = origin + 120_000_000
    presents = [int(row["utc_us"]) for row in rows(trial / "frame-times.csv")]
    if not presents or presents[-1] < end or presents != sorted(presents):
        raise ValueError("Incomplete or unordered presentation trace")
    intervals = set()
    threads = Counter()
    for row in rows(trial / "thread-cpu.csv"):
        finish = int(row["utc_us"])
        start = finish - int(row["interval_us"])
        if origin <= start < finish <= end:
            intervals.add((start, finish))
            name = row["thread_name"]
            if name == "victory-submit" or name.startswith(("victory-list-", "victory-under")):
                threads[name] += int(row["cpu_us"])
    previous = origin
    counted = 0
    for start, finish in sorted(intervals):
        if start < previous:
            raise ValueError("Overlapping CPU sampling intervals")
        counted += bisect_right(presents, finish) - bisect_right(presents, start)
        previous = finish
    if not counted:
        raise ValueError("Missing CPU samples")
    totals = defaultdict(int)
    previous = None
    label = "parallel copy recording and descriptor preparation"
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    with (trial / "runtime.log").open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if label not in line:
                continue
            line = ansi.sub("", line)
            finish = round(datetime.fromisoformat(line.split()[0].replace("Z", "+00:00")).timestamp() * 1e6)
            if previous is not None and origin <= previous < finish <= end:
                for key in ("sampled", "overlapped", "overlap_us"):
                    totals[key] += int(re.search(rf"\b{key}=(\d+)", line)[1])
            previous = finish
    return {
        "route_presents": bisect_right(presents, end) - bisect_right(presents, origin),
        "cpu_sample_presents": counted,
        "cpu_ms_per_present_by_thread": {n: round(v / counted / 1000, 3) for n, v in sorted(threads.items())},
        "sampled_batches": totals["sampled"], "overlapping_batches": totals["overlapped"],
        "longest_intersection_us_summed_over_sampled_batches": totals["overlap_us"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cell", action="store_true")
    args = parser.parse_args()
    result = measure(args.trial, "cell-begin-ms.txt" if args.cell else "walk-start.txt")
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
