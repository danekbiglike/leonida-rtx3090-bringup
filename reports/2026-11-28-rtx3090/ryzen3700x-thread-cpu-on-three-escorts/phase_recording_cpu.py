"""Match the CPU time of named renderer threads to actual presented frames."""
import argparse
import csv
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path


def samples(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def export(trial, output):
    origin = int((trial / "walk-start.txt").read_text()) * 1000
    finish = origin + 120_000_000
    presents = [int(row["utc_us"]) for row in samples(trial / "frame-times.csv")]
    if presents != sorted(presents) or not presents or presents[-1] < finish:
        raise ValueError("This route lacks a complete present trace")
    intervals = defaultdict(lambda: defaultdict(int))
    for row in samples(trial / "thread-cpu.csv"):
        end = int(row["utc_us"])
        start = end - int(row["interval_us"])
        if start < origin or end > finish or start >= end:
            continue
        name = row["thread_name"]
        if name == "victory-submit":
            group = "submit"
        elif name.startswith("victory-list-"):
            group = "list_recording"
        elif name.startswith("victory-wide-"):
            group = "refresh_workers"
        elif name:
            group = "other_named"
        else:
            group = "unnamed"
        intervals[start, end][group] += int(row["cpu_us"])
    groups = ("submit", "list_recording", "refresh_workers", "other_named", "unnamed")
    previous = origin
    with output.open("w", encoding="ascii", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("start_us", "end_us", "presents", *(g + "_cpu_us" for g in groups)))
        for (start, end), counts in sorted(intervals.items()):
            if start < previous:
                raise ValueError("Overlapping thread sample intervals")
            previous = end
            frames = bisect_right(presents, end) - bisect_right(presents, start)
            writer.writerow((start-origin, end-origin, frames, *(counts[g] for g in groups)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.trial, args.output)
