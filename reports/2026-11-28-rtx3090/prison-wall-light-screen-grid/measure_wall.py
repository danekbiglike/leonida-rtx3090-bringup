"""Measure whether straight boundaries of two wall highlights follow the screen grid."""
import argparse
import csv
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw


def boundary_positions(rgb, origin, threshold):
    left, top = origin
    mask = [[r >= threshold and r - g > 20 and g - b > 22 for (r, g, b) in
             (rgb.getpixel((x, y)) for x in range(rgb.width))] for y in range(rgb.height)]
    def by_row(rows, origin):
        edges = Counter()
        for index in range(1, len(rows)):
            run = 0
            for change in [a != b for a, b in zip(rows[index], rows[index-1])] + [False]:
                if change:
                    run += 1
                else:
                    if run >= 6:
                        edges[origin+index] += run
                    run = 0
        return edges
    return by_row(list(zip(*mask)), left), by_row(mask, top)


def sweep(edges, pitch, origin):
    # Edges are recorded at the first pixel on the other side of the threshold.
    # Its boundary is halfway between the two pixel centres.
    return [sum(weight for at, weight in edges.items()
                if abs((at - origin - pitch * phase / 64 + pitch/2) % pitch - pitch/2) <= 1.25)
            for phase in range(64)]


def measure(first, second, output, from_sheet):
    rect = (754, 200, 1027, 353)
    sheet = Image.new("RGB", (546, 180))
    draw = ImageDraw.Draw(sheet)
    with (output / "wall-boundaries.csv").open("w", encoding="ascii", newline="") as dest:
        rows = csv.writer(dest, lineterminator="\n")
        rows.writerow(("view","threshold","axis","period_px","straight_edge_px","on_grid_px",
                       "half_period_px","best_phase_64","best_px"))
        for col, (profile, path, client) in enumerate([
                ("stepped", first, (3,31,1818,993)), ("smooth", second, (3,25,1818,993))]):
            with Image.open(path) as im:
                box = (273*col, 24, 273*(col+1), 177) if from_sheet else rect
                crop = im.crop(box).convert("RGB")
                sheet.paste(crop, (273*col, 24))
                draw.text((273*col+5,5),profile,fill="white")
                for threshold in (150,175,190,205):
                    edges = boundary_positions(crop, rect[:2], threshold)
                    for axis, hits, pitch, origin in zip(("x","y"), edges, (client[2]/160,client[3]/90),client[:2]):
                        counts = sweep(hits, pitch, origin)
                        rows.writerow((profile,threshold,axis,round(pitch,4),sum(hits.values()),
                                       counts[0],counts[32],counts.index(max(counts)),max(counts)))
    sheet.save(output / "wall-crops.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stepped", type=Path)
    ap.add_argument("smooth", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--from-sheet", action="store_true", help="supply the published two-crop sheet for both inputs")
    args = ap.parse_args()
    measure(args.stepped, args.smooth, args.output, args.from_sheet)
