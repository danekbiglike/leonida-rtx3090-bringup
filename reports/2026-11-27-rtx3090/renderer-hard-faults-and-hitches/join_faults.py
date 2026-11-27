"""Align one-second process hard-fault observations with the actual gaps between presents."""
import bisect
import csv
import json
from pathlib import Path
import statistics
import sys


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize(trace, dest):
    faults = read(trace/"process-faults.csv")
    disk = read(trace/"disk-faults.csv")
    presents = [int(r["utc_us"]) for r in read(trace/"frame-times.csv")]
    stamps = [round(float(r["utc_s"])*1e6) for r in disk]
    output = []
    for a, b in zip(faults, faults[1:]):
        low, high = int(a["utc_us"]), int(b["utc_us"])
        if low < presents[0] or high > presents[-1] or not stamps:
            continue
        index = bisect.bisect_left(stamps, high)
        nearest = min(range(max(0, index-1), min(len(stamps),index+1)), key=lambda i: abs(stamps[i]-high))
        if abs(stamps[nearest]-high) > 600_000:
            continue
        d = disk[nearest]
        duration = high-low
        covered = 0
        start = bisect.bisect_right(presents, low)
        end = bisect.bisect_left(presents, high)
        for i in range(start, end+1):
            if presents[i]-presents[i-1] >= 500_000:
                covered += max(0, min(high,presents[i])-max(low,presents[i-1]))
        output.append(dict(end_utc_us=high, interval_s=round(duration/1e6,4),
                           disk_counter_skew_ms=round((stamps[nearest]-high)/1000,2),
                           long_frame_fraction=round(covered/duration,4),
                           process_hard_faults_s=round((int(b["hard_faults"])-int(a["hard_faults"]))*1e6/duration,2),
                           paging_disk_read_mib_s=round(float(d["paging_disk_read_bytes_s"])/2**20,3),
                           game_disk_read_mib_s=round(float(d["game_disk_read_bytes_s"])/2**20,3),
                           available_physical_mib=float(d["available_physical_mib"])))
    dest.mkdir(exist_ok=True, parents=True)
    with (dest/"intervals.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=list(output[0]),lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    groups={"at_least_half_in_long_frames":[r for r in output if r["long_frame_fraction"] >= .5],
            "no_long_frames":[r for r in output if r["long_frame_fraction"]==0]}
    result={"report_id":"danekbiglike/rtx3090-20261127-process-hard-faults","matched_intervals":len(output)}
    for group, rows in groups.items():
        result[group]={"intervals":len(rows)}
        if rows:
            for field in ("process_hard_faults_s","paging_disk_read_mib_s","game_disk_read_mib_s","available_physical_mib"):
                result[group]["median_"+field]=round(statistics.median(r[field] for r in rows),3)
                result[group]["mean_"+field]=round(statistics.mean(r[field] for r in rows),3)
    (dest/"metrics.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result))


if __name__ == "__main__":
    summarize(Path(sys.argv[1]),Path(sys.argv[2]))
