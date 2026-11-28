"""Estimate minimum user-mode time of the busiest thread inside one long frame."""
import argparse
import collections
import csv
import json
from pathlib import Path


def records(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def analyze(trial, end):
    frame = next(r for r in records(trial / "frame-times.csv") if int(r["utc_us"]) == end)
    length = int(frame["present_interval_us"])
    process = [r for r in records(trial / "process-activity.csv") if end-length <= int(r["utc_us"]) <= end]
    if len(process) < 2:
        raise ValueError("Too few process observations inside the frame")
    first, last = (int(r["utc_us"]) for r in (process[0], process[-1]))
    hot = collections.Counter()
    intervals = set()
    for r in records(trial / "thread-cpu.csv"):
        finish, duration = int(r["utc_us"]), int(r["interval_us"])
        if first <= finish-duration and finish <= last:
            hot[int(r["thread_id"])] += int(r["cpu_us"])
            intervals.add((finish, duration))
    if not hot:
        raise ValueError("No thread intervals nested inside the process interval")
    tid, cpu = hot.most_common(1)[0]

    def delta(field):
        return int(process[-1][field]) - int(process[0][field])

    kernel = delta("kernel_100ns") // 10
    return dict(frame_end_utc_us=end, frame_us=length, process_start_utc_us=first, process_end_utc_us=last,
                process_wall_us=last-first, process_kernel_us=kernel, process_user_us=delta("user_100ns")//10,
                process_read_bytes=delta("read_bytes"), thread_intervals=len(intervals),
                thread_window_us=sum(d for _, d in intervals), top_thread_id=tid, top_thread_cpu_us=cpu,
                top_thread_estimated_min_user_us=max(0, cpu-kernel))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("frame_end_utc_us", type=int)
    args = parser.parse_args()
    print(json.dumps(analyze(args.trial, args.frame_end_utc_us), indent=2))
