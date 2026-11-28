"""Export complete device queue telemetry windows inside a measured prison escort."""
import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


QUEUE = re.compile(
    r"nothing of ours queued ([\d.]+) ms \(the card about (\d+)% busy by this count\), "
    r"([\d.]+) ms of that while the submitting thread was working .*? "
    r"the submitting thread stood waiting for the card ([\d.]+) ms"
)
STAMP = re.compile(r"\d{4}-\d\d-\d\dT[\d:.]+Z")


def export(trial, destination):
    begin = int((trial / "walk-start.txt").read_text(encoding="ascii")) / 1000
    previous = None
    with (trial / "runtime.log").open(encoding="utf-8", errors="replace") as log, destination.open(
        "w", encoding="ascii", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(("start_s", "end_s", "queue_empty_ms_per_frame", "queue_occupied_percent",
                         "queue_empty_while_submit_active_ms_per_frame", "submit_wait_for_card_ms_per_frame"))
        for line in log:
            match = QUEUE.search(line)
            if not match:
                continue
            now = datetime.fromisoformat(STAMP.search(line)[0].replace("Z", "+00:00")).timestamp()
            if previous is not None and begin <= previous < now <= begin + 120:
                writer.writerow((round(previous - begin, 4), round(now - begin, 4), *match.groups()))
            previous = now


def export_process_cpu(trial, destination, logical_processors):
    if logical_processors < 1:
        raise ValueError("A positive logical processor count is required")
    origin = int((trial / "walk-start.txt").read_text(encoding="ascii")) * 1000
    previous = None
    with (trial / "process-activity.csv").open(encoding="utf-8-sig", newline="") as log, destination.open(
        "w", encoding="ascii", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(("start_us", "end_us", "process_cpu_100ns", "logical_processors", "machine_cpu_percent"))
        for row in csv.DictReader(log):
            end = int(row["utc_us"])
            if not origin <= end <= origin + 120_000_000:
                continue
            cpu = int(row["user_100ns"]) + int(row["kernel_100ns"])
            if previous is not None:
                start, last_cpu = previous
                if end <= start or cpu < last_cpu:
                    raise ValueError("Process counters regressed inside this walk")
                used = cpu - last_cpu
                share = 100 * used / (10 * (end - start) * logical_processors)
                writer.writerow((start - origin, end - origin, used, logical_processors, round(share, 4)))
            previous = end, cpu


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--process-usage", type=Path)
    parser.add_argument("--logical-processors", type=int)
    args = parser.parse_args()
    export(args.trial, args.destination)
    if args.process_usage:
        if args.logical_processors is None:
            parser.error("--process-usage requires --logical-processors")
        export_process_cpu(args.trial, args.process_usage, args.logical_processors)
