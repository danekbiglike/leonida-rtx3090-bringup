"""Compare complete Present intervals on either side of VIctory's copy-refresh toggle."""
import argparse
import csv
import json
import math
import re
from bisect import bisect_right
from datetime import datetime
from pathlib import Path
from statistics import median

ANSI = re.compile(r"\x1b\[[\d;]*m")
TOGGLE = re.compile(r"\(VICTORY_COPY_CHANGED=alt\): (ON|off, as usual)\s*$")


def wall_time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.utcoffset() is None:
        raise ValueError("anchor and log timestamps must include a timezone")
    return stamp


def describe(rows):
    if not rows:
        return None
    times = sorted(duration for duration, _ in rows)
    total = sum(times)
    return dict(frames=len(times), seconds=total / 1e6, fps=len(times) * 1e6 / total,
                p50_ms=median(times) / 1000, p95_ms=times[math.ceil(.95 * len(times)) - 1] / 1000,
                max_ms=times[-1] / 1000, over_200ms=sum(t > 200000 for t in times),
                mean_draws=sum(draws for _, draws in rows) / len(rows))


def compare(frame_file, log_file, anchor, start, seconds, guard):
    if not all(map(math.isfinite, (start, seconds, guard, anchor["seen"]))) or start < 0 or seconds <= 0 or guard < 0:
        raise ValueError("invalid measurement interval")
    origin = wall_time(anchor["utc"])
    edges, states = [], []
    with log_file.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            line = ANSI.sub("", raw)
            match = TOGGLE.search(line)
            if not match:
                continue
            at = anchor["seen"] + (wall_time(line.split()[0]) - origin).total_seconds()
            state = "changed_chunks" if match[1] == "ON" else "whole_ranges"
            if states and (at <= edges[-1] or state == states[-1]):
                raise ValueError("discontinuous toggle log")
            states.append(state)
            edges.append(at)
    stop = start + seconds
    if len(edges) < 2 or edges[0] > start or edges[-1] < stop:
        raise ValueError("need toggle events bracketing the full measurement")
    blocks = [[] for _ in edges]
    elapsed = 0
    excluded = []
    with frame_file.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            duration = int(row["present_interval_us"])
            if duration <= 0:
                raise ValueError("invalid present interval")
            begin = elapsed / 1e6
            elapsed += duration
            end = elapsed / 1e6
            if begin >= stop:
                break
            if end <= start:
                continue
            sample = (duration, int(row["draw_calls"]))
            index = bisect_right(edges, begin) - 1
            if (index < 0 or index + 1 >= len(edges) or begin < start or end > stop
                    or begin < edges[index] + guard or end > edges[index + 1] - guard):
                excluded.append(sample)
                continue
            blocks[index].append(sample)
    if elapsed / 1e6 < stop:
        raise ValueError("frame capture ends before measurement")
    by_state = {name: [] for name in ("whole_ranges", "changed_chunks")}
    report = []
    for index, samples in enumerate(blocks):
        if samples:
            by_state[states[index]].extend(samples)
            report.append(dict(mode=states[index], toggle_seconds=edges[index],
                               **describe(samples)))
    if not all(by_state.values()):
        raise ValueError("no complete frames in one of the modes")
    return dict(start_seconds=start, duration_seconds=seconds, guard_seconds=guard,
                excluded=describe(excluded), blocks=report,
                modes={key: describe(value) for key, value in by_state.items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ["frames", "log", "anchor"]:
        parser.add_argument(field, type=Path)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--guard", type=float, default=1)
    args = parser.parse_args()
    print(json.dumps(compare(args.frames, args.log, json.loads(args.anchor.read_text(encoding="utf-8-sig")),
                             args.start, args.seconds, args.guard), indent=2))
