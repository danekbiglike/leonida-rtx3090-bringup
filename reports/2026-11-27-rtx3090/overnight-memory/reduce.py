"""Reduce the November 26 worker-off RTX 3090 run to anonymous hourly measurements."""

import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median


REPORT_ID = "danekbiglike/rtx3090-20261127-memory-11h"
# The launcher created memory.csv just before starting its process-uptime clock.
START_UTC = datetime.fromisoformat("2026-11-26T18:17:56.527644+00:00")
LOG_PATTERNS = {
    "mirror_mib": re.compile(r"host copies in the card's memory: \d+ copies (\d+) MB"),
    "depth_twins": re.compile(r"depth twins: (\d+) alive"),
    "indexed_slots": re.compile(r"the queue: (\d+) slots"),
    "dxgi": re.compile(r"the card's own: budget \d+ MB, in use (\d+) MB.*?"
                       r"the PC's shared with the card: budget \d+ MB, in use (\d+) MB"),
}
ANSI = re.compile(r"\x1b\[[\d;]*[mK]")


def reduce_run(trace_dir, output):
    bins = defaultdict(lambda: defaultdict(list))
    with (trace_dir / "memory.csv").open(encoding="ascii", newline="") as source:
        for row in csv.DictReader(source):
            group = bins[int(row["uptime_ms"]) // 3_600_000]
            for field in ("uptime_ms", "private_bytes", "working_set_bytes", "job_peak_bytes",
                          "physical_available_bytes"):
                group[field].append(int(row[field]))

    with (trace_dir / "runtime.log").open(encoding="utf-8", errors="replace") as source:
        for line in source:
            for field, pattern in LOG_PATTERNS.items():
                match = pattern.search(line)
                if not match:
                    continue
                timestamp = ANSI.sub("", line).split(maxsplit=1)[0]
                elapsed = (datetime.fromisoformat(timestamp.replace("Z", "+00:00")) - START_UTC).total_seconds()
                hour = int(elapsed // 3600)
                if hour not in bins:
                    continue
                if field == "dxgi":
                    bins[hour]["dedicated_mib"].append(int(match[1]))
                    bins[hour]["shared_mib"].append(int(match[2]))
                else:
                    bins[hour][field].append(int(match[1]))

    log_fields = ("dedicated_mib", "shared_mib", "mirror_mib", "depth_twins", "indexed_slots")
    with output.open("w", encoding="utf-8", newline="") as dest:
        writer = csv.writer(dest, lineterminator="\n")
        writer.writerow(["report_id", "hour", "memory_samples", "last_uptime_ms", "median_private_bytes",
                         "median_working_set_bytes", "job_peak_bytes", "min_system_available_bytes",
                         *(f"median_{field}" for field in log_fields)])
        for hour, group in sorted(bins.items()):
            writer.writerow([REPORT_ID, hour + 1, len(group["uptime_ms"]), max(group["uptime_ms"]),
                             median(group["private_bytes"]), median(group["working_set_bytes"]),
                             max(group["job_peak_bytes"]), min(group["physical_available_bytes"]),
                             *(median(group[field]) if group[field] else "" for field in log_fields)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path, help="directory containing memory.csv and runtime.log")
    parser.add_argument("output", type=Path, help="hourly output CSV")
    args = parser.parse_args()
    reduce_run(args.trace_dir, args.output)
