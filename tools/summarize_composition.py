"""Summarize the local composition probes without printing resource handles or game identifiers."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re


def summarize(path):
    displayed = set()
    targets = {}
    draw_tables = defaultdict(set)
    sources = defaultdict(set)
    image_ids = {}
    draws = Counter()
    scopes = Counter()
    readbacks = []
    samples = []
    with path.open(encoding="utf-8", errors="replace") as log:
        for line in log:
            if "display source " in line:
                m = re.search(r"display source ([\da-fA-F]+)", line)
                if m:
                    displayed.add(int(m[1], 16))
            elif "[frame-probe] draw " in line:
                m = re.search(r"draw (\d+) .*?first RTV ([\da-fA-F]+)", line)
                if m:
                    targets[int(m[1])] = int(m[2], 16)
            elif "draw-table draw=" in line:
                m = re.search(r"draw=(\d+) word=\d+ id=([\da-fA-F]+)", line)
                if m:
                    draw_tables[int(m[1])].add(int(m[2], 16))
            elif "image-resource=" in line:
                m = re.search(r"image-resource=([\da-fA-F]+) texture-key=([\da-fA-F]+)", line)
                if m:
                    image_ids[int(m[2], 16)] = int(m[1], 16)
            elif "sampled-table=" in line:
                m = re.search(r"sampled-table=([\da-fA-F]+) slot=\d+ texture-key=([\da-fA-F]+) mip=(\d+) layer=(\d+)", line)
                if m:
                    key = int(m[2], 16)
                    if key in image_ids:
                        sources[int(m[1], 16)].add((image_ids[key], int(m[3]), int(m[4])))
            elif "draw-route batch=" in line:
                m = re.search(r"target=([\da-fA-F]+)", line)
                if m:
                    draws[int(m[1], 16)] += 1
            elif "table-scan id=" in line:
                m = re.search(r"inspected=(\d+) populated=([\da-fA-F]+) images=([\da-fA-F]+) matched=([\da-fA-F]+)", line)
                if m:
                    scopes[int(m[1]), *(int(v, 16) for v in m.groups()[1:])] += 1
            elif "after-draw=" in line:
                m = re.search(r"target=([\da-fA-F]+).*?pixels=(\d+) nonblack=(\d+) hr=00000000", line)
                if m:
                    readbacks.append((int(m[1], 16), int(m[2]), int(m[3])))
            elif "RGB sample" in line:
                m = re.search(r"nonblack (\d+) of (\d+)", line)
                if m:
                    samples.append(int(m[1]))

    print(f"Submitted draws: {sum(draws.values())}; into display sources: {sum(draws[t] for t in displayed)}.")
    intermediate = set(draws) - displayed
    display_tables = {t for n, tables in draw_tables.items() if targets.get(n) in displayed for t in tables}
    mapped = {t for t in display_tables if sources[t]}
    linked = {t for t in mapped if any(r in intermediate and mip == layer == 0 for r, mip, layer in sources[t])}
    print(f"Recorded display-table handles: {len(display_tables)}; with a matched image and known resource: "
          f"{len(mapped)}; containing an intermediate target at mip 0, layer 0: {len(linked)}.")
    for (slots, populated, images, matched), count in sorted(scopes.items()):
        print(f"{count} table scans: {slots} slots, populated mask {populated:#x}, image mask {images:#x}, "
              f"matched image mask {matched:#x}.")
    for label, subset in (("intermediate", intermediate), ("display", displayed)):
        reads = [r for r in readbacks if r[0] in subset]
        print(f"{label.capitalize()} target reads: {len(reads)}; with nonblack RGB: {sum(r[2] > 0 for r in reads)}.")
    print(f"Swapchain samples: {len(samples)}; with nonblack RGB: {sum(v > 0 for v in samples)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_log", type=Path)
    summarize(parser.parse_args().runtime_log)

