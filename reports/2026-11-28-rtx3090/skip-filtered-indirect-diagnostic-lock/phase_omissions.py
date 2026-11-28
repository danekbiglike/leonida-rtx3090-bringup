"""Read renderer drop and pipeline-lookup counters in complete, gate-aligned reporting windows."""
import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


COUNTS = re.compile(
    r"dropped (\d+) without a host pipeline \((\d+) being made\) and "
    r"(\d+) indirect \((\d+) of all these left out on purpose"
)
UTC = re.compile(r"\d{4}-\d\d-\d\dT[\d:.]+Z")


def windows(log, origin):
    previous = None
    for line in log:
        counts = COUNTS.search(line)
        if not counts:
            continue
        end = datetime.fromisoformat(UTC.search(line)[0].replace("Z", "+00:00")).timestamp()
        if previous is not None and origin <= previous < end <= origin + 120:
            direct, pending, indirect, skipped = map(int, counts.groups())
            # The renderer rounds each per-frame rate separately. Keep the
            # signed residual so small rounding differences remain visible.
            yield (round(previous-origin, 4), round(end-origin, 4), direct, indirect,
                   skipped, direct+indirect-skipped, pending)
        previous = end


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    origin = int((args.trial / "walk-start.txt").read_text()) / 1000
    with (args.trial / "runtime.log").open(encoding="utf-8", errors="replace") as log:
        rows = list(windows(log, origin))
    if not rows:
        raise SystemExit("No complete renderer reports during the 120-second route")
    with args.output.open("w", encoding="ascii", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(("start_s", "end_s", "direct_dropped_per_frame", "indirect_dropped_per_frame",
                         "marked_pipeline_lookups_per_frame", "drops_minus_marked_lookups_per_frame", "pipelines_building"))
        writer.writerows(rows)
