"""Compare complete alternating GPU-helper phases inside a scored game interval."""
import argparse
import csv
import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ANSI_STYLE = re.compile(r"\x1b\[[\d;]*m")


def transitions(log):
    for line in log:
        if "the card is kept awake, by turns" not in line:
            continue
        line = ANSI_STYLE.sub("", line)
        state = re.search(r"\bon=(true|false)\b", line)
        stamp = re.search(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z", line)
        if not state or not stamp:
            raise ValueError("GPU helper transition lacks a state or UTC time")
        dt = datetime.fromisoformat(stamp[0].replace("Z", "+00:00"))
        yield round(dt.timestamp() * 1_000_000), state[1]


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def thread_samples(path):
    by_interval = defaultdict(int)
    seen_helper = False
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            end = int(row["utc_us"])
            span = int(row["interval_us"])
            if span <= 0:
                raise ValueError("Non-positive thread sampling interval")
            cost = 0
            if row["thread_name"] == "victory-card-awake":
                seen_helper = True
                cost = int(row["cpu_us"])
            # Windows logs only threads with a positive CPU delta. Work by
            # other threads confirms a sample even if the helper slept.
            by_interval[end-span, end] += cost
    if not seen_helper:
        raise ValueError("The helper did not appear in the thread trace")
    return by_interval


def compare(trial, phase, cpu):
    marker = "walk-start.txt" if phase == "escort" else "cell-begin-ms.txt"
    origin = int((trial / marker).read_text().strip()) * 1000
    data = trial / ("measured-" + phase)
    frames = read_rows(data / "frames.csv")
    board = read_rows(data / "gpu.csv")
    with (trial / "runtime.log").open(encoding="utf-8", errors="replace") as stream:
        switches = list(transitions(stream))
    for (begin, state), (end, other) in zip(switches, switches[1:]):
        if state == other or not 19_000_000 <= end-begin <= 21_000_000:
            continue
        if begin < origin or end > origin + 120_000_000:
            continue
        # The log marks the first submission after a switch. Drop one second at
        # each end so board sampling and a boundary-crossing frame can settle.
        left, right = begin-origin+1_000_000, end-origin-1_000_000
        selected = [r for r in frames if left <= int(r["elapsed_us"]) < right]
        intervals = sorted(int(r["present_interval_us"]) for r in selected
                           if int(r["elapsed_us"])-int(r["present_interval_us"]) >= left)
        hardware = [r for r in board if left <= float(r["elapsed_s"])*1e6 < right]
        if not selected or not intervals or not hardware:
            raise ValueError(f"Missing samples inside a complete {phase} phase")
        full = [(b-a, cost) for (a, b), cost in cpu.items()
                if origin+left <= a < b <= origin+right]
        covered = sum(span for span, _ in full)
        if covered < (right-left)*0.65:
            raise ValueError(f"Insufficient CPU sampling during {phase} at {left/1e6:.3f} s")
        yield dict(phase=phase, helper=state, start_s=round(left/1e6, 3),
                   end_s=round(right/1e6, 3), presents=len(selected),
                   fps=round(len(selected)*1e6/(right-left), 3),
                   p95_ms=round(intervals[(95*len(intervals)+99)//100-1]/1000, 3),
                   median_draws=statistics.median(int(r["draw_calls"]) for r in selected),
                   board_samples=len(hardware),
                   mean_gpu_busy_pct=round(statistics.mean(float(r["gpu_percent"]) for r in hardware), 2),
                   cpu_sample_s=round(covered/1e6, 3),
                   helper_cpu_ms_per_s=round(1000*sum(cost for _, cost in full)/covered, 2),
                   mean_board_w=round(statistics.mean(float(r["board_power_w"]) for r in hardware), 2),
                   median_clock_mhz=statistics.median(float(r["graphics_clock_mhz"]) for r in hardware))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    cpu = thread_samples(args.trial / "thread-cpu.csv")
    for phase in ("cell", "escort"):
        if (args.trial / ("measured-"+phase) / "frames.csv").is_file():
            rows.extend(compare(args.trial, phase, cpu))
    if not rows:
        raise SystemExit("No complete logged GPU-helper phases inside a scored interval")
    with args.output.open("w", encoding="ascii", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
