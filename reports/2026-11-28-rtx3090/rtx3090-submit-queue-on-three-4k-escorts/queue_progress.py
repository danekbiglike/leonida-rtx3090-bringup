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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    export(args.trial, args.destination)
