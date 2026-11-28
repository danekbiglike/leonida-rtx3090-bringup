"""Pair GPU dispatch times by scene and round, verifying the complete sampling grid."""
import csv
import statistics
import sys
from pathlib import Path


def summarize(source):
    with source.open(encoding="ascii", newline="") as stream:
        data = list(csv.DictReader(stream))
    pairs = {}
    for r in data:
        key = (int(r["depth_w"]), r["pass"], int(r["scene"]), int(r["round"]))
        slot = (key, int(r["cached"]))
        if slot in pairs:
            raise ValueError(f"Duplicate observation {slot}")
        pixels = int(r["output_w"]) * int(r["output_h"])
        if int(r["compared_pixel_bytes"]) != pixels * 4 or int(r["compared_cell_bytes"]) != 995344:
            raise ValueError(f"Incomplete readback {slot}")
        pairs[slot] = float(r["gather_us"]) + float(r["resolve_us"])
    if len(pairs) != 168:
        raise ValueError(f"{source} has {len(pairs)} observations")
    for w in (1297, 2560, 3840):
        for kind in ("diffuse", "reflection"):
            for scene in (1, 2):
                keys = [(w, kind, scene, i) for i in range(7)]
                times = [[pairs[k, v] for k in keys] for v in (0, 1)]
                median = [statistics.median(series) for series in times]
                yield [source.stem, w, kind, scene, *[round(m, 3) for m in median],
                       round(statistics.median(a-b for a,b in zip(*times)), 3)]


if __name__ == "__main__":
    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow(["run","depth_width","pass","scene","baseline_us","candidate_us","median_paired_saving_us"])
    for arg in sys.argv[1:]:
        out.writerows(summarize(Path(arg)))
