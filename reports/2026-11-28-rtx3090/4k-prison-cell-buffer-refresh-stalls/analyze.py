"""Join slow in-cell presents to single-frame VIctory reports and OS samples."""
import argparse
import bisect
import csv
import re
from datetime import datetime, timezone
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]


def save(path, values):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=values[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def utc_us(timestamp):
    date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    elapsed = date - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return elapsed // datetime.resolution


def profile(path):
    output = []
    group = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if not line.startswith("20"):
            continue
        if "the card's clock per frame:" in line:
            match = re.search(r"queued ([\d.]+) ms .*? ([\d.]+) ms of that", line)
            group = {}
            if match:
                group.update(card_queue_idle_ms=match[1], card_idle_during_submit_ms=match[2])
        elif "preparing per frame, the submitting thread:" in line:
            match = re.search(r"thread: ([\d.]+) ms .*?\(refreshes ([\d.]+) in (\d+) flushes of (\d+)", line)
            if match:
                group.update(utc_us=utc_us(line.split()[0]), submit_ms=match[1], refresh_ms=match[2],
                             batches=match[3], requested=match[4])
        elif "texture refreshes per frame, all threads:" in line and "utc_us" in group:
            match = re.search(r"all threads: ([\d.]+) ms", line)
            if match:
                group["texture_ms"] = match[1]
                output.append(group)
            group = {}
    return output


def analyze(trial, dest):
    begin = int((trial / "cell-begin-ms.txt").read_text()) * 1000
    frames = rows(trial / "frame-times.csv")
    ticks = [f["utc_us"] for f in frames]
    reports = profile(trial / "runtime.log")
    report_times = [r["utc_us"] for r in reports]
    report_fields = ("submit_ms", "refresh_ms", "batches", "requested",
                     "card_queue_idle_ms", "card_idle_during_submit_ms", "texture_ms")
    stalls = []
    for f in frames:
        end = f["utc_us"]
        if not begin <= end < begin + 120_000_000 or f["present_interval_us"] < 500_000:
            continue
        # The renderer emits the report just after Present. Require a tight match,
        # then count presents between that report and its predecessor.
        i = bisect.bisect_left(report_times, end)
        r = reports[i] if 0 < i < len(reports) and report_times[i] - end < 5_000 else None
        count = bisect.bisect_right(ticks, report_times[i]) - bisect.bisect_right(ticks, report_times[i-1]) if r else 0
        stalls.append(dict(present_utc_us=end, interval_us=f["present_interval_us"], draws=f["draw_calls"],
                           presents_in_matched_report=count if r else "",
                           **{key: r.get(key, "") if count == 1 else "" for key in report_fields}))
    save(dest / "slow-presents.csv", stalls)
    longest = max(stalls, key=lambda s: s["interval_us"])
    end = longest["present_utc_us"]
    start = end - longest["interval_us"]
    activity = rows(trial / "process-activity.csv")
    memory = {m["utc_us"]: m for m in rows(trial / "memory.csv")}
    samples = []
    for a, b in zip(activity, activity[1:]):
        if a["utc_us"] < start or b["utc_us"] > end:
            continue
        m, n = memory[a["utc_us"]], memory[b["utc_us"]]
        delta = b["utc_us"] - a["utc_us"]
        samples.append(dict(start_utc_us=a["utc_us"], end_utc_us=b["utc_us"],
                            cpu_core_equivalents=round(sum(b[k]-a[k] for k in ("kernel_100ns","user_100ns")) / (10*delta), 3),
                            process_read_bytes=b["read_bytes"]-a["read_bytes"],
                            process_page_faults=n["page_fault_count"]-m["page_fault_count"],
                            free_system_bytes=n["physical_available_bytes"]))
    save(dest / "longest-frame-os.csv", samples)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("dest", type=Path)
    args = parser.parse_args()
    analyze(args.trial, args.dest)
