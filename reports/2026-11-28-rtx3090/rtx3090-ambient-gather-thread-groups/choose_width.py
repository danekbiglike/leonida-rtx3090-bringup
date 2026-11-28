"""Choose a gather width only after exact-output checks and paired GPU timings."""
import csv
import statistics
import sys
from pathlib import Path


def choose(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    values = {(int(r["scene"]), int(r["round"]), int(r["group_width"])): float(r["gpu_us"]) for r in rows}
    expected = {(s, r, w) for s in (1, 2) for r in range(9) for w in (8, 16, 32)}
    if (len(rows) != len(expected) or values.keys() != expected or
            any(int(r["verified_bytes"]) != 691200 or int(r["group_height"]) != 2 for r in rows) or
            not all(0 < t < 1e6 for t in values.values())):
        raise ValueError("Incomplete GPU measurements")
    choices = [(1.0, 8)]
    for width in (16, 32):
        medians = []
        for scene in (1, 2):
            ratios = [values[scene, r, width] / values[scene, r, 8] for r in range(9)]
            medians.append(statistics.median(ratios))
            if sum(x < 1 for x in ratios) < 7:
                break
        else:
            if max(medians) < 0.97:
                choices.append((max(medians), width))
    return min(choices)[1]


if __name__ == "__main__":
    print(choose(Path(sys.argv[1])))
