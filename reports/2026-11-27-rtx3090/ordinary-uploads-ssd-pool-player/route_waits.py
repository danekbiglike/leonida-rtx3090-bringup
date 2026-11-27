"""Export timed renderer synchronization measurements from a marked walk."""
import argparse
import csv
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median


DATE = re.compile(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}")
CLOCK = re.compile(
    r"the card's clock per frame: nothing of ours queued ([\d.]+) ms .*?, "
    r"([\d.]+) ms of that while the submitting thread was working .*?; "
    r"the submitting thread stood waiting for the card ([\d.]+) ms"
)
SCAN = re.compile(
    r"pieces of 64 KiB compared on the card per frame, by copy: (\d+) in "
    r"\d+ copies \((\d+) MB read a frame\), (\d+) of them found changed"
)


def export(trial, report):
    start = int((trial / "walk-start.txt").read_text()) / 1000
    fields = ("elapsed_s", "nothing_queued_ms", "idle_while_submitting_ms",
              "submit_wait_ms", "pieces_compared", "compare_mb", "pieces_changed")
    rows = []
    with (trial / "runtime.log").open(encoding="utf8", errors="replace") as stream:
        current = None
        clock = None
        for line in stream:
            sample = CLOCK.search(line)
            scan = SCAN.search(line)
            if not (sample or scan):
                continue
            stamp = DATE.search(line)[0]
            if sample:
                current, clock = stamp, tuple(map(float, sample.groups()))
            elif current == stamp and clock is not None:
                moment = datetime.strptime(stamp, "%d/%m/%Y %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=3)))
                elapsed = moment.timestamp() - start
                if 0 <= elapsed < 120:
                    rows.append((round(elapsed, 3), *clock, *map(int, scan.groups())))
                clock = None
    if not rows:
        raise ValueError("No paired clock and compare reports in the marked walk")
    with report.open("w", encoding="utf8", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)
    print(len(rows), dict(zip(fields[1:], map(median, zip(*(row[1:] for row in rows))))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    export(args.trial, args.csv_path)
