"""Export measured presents and a marked figure from the original local captures."""

import argparse
import csv
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


REPORT = "danekbiglike/rtx3090-20261127-br-hdd-gate"


def write_frames(trace, dest):
    start = int((trace / "walk-start.txt").read_text().strip()) * 1000
    with (trace / "frame-times.csv").open(newline="") as src, dest.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["report_id", "elapsed_us", "present_interval_us", "draw_calls"])
        last = None
        count = 0
        for row in csv.DictReader(src):
            last = int(row["utc_us"]) - start
            if 0 <= last < 120_000_000:
                writer.writerow([REPORT, last, int(row["present_interval_us"]), int(row["draw_calls"])])
                count += 1
        if last is None or last < 120_000_000 or count != 1122:
            raise ValueError("unexpected route or incomplete frame capture")


def write_figure(images, dest):
    panels = [("During the first minute of timed input", "hdd-walk-near-start.jpg"),
              ("At the closed gate after timed input ended", "hdd-walk-end.jpg")]
    width = 1480
    font = ImageFont.load_default(size=23)
    small = ImageFont.load_default(size=18)
    images_and_titles = []
    for title, name in panels:
        with Image.open(images / name) as shot:
            frame = ImageOps.contain(shot.convert("RGB"), (width, 1200), Image.Resampling.LANCZOS)
        images_and_titles.append((title, frame))
    figure = Image.new("RGB", (width, sum(52 + frame.height for _, frame in images_and_titles)), "#141923")
    draw = ImageDraw.Draw(figure)
    y = 0
    for title, frame in images_and_titles:
        draw.text((16, y + 10), title, fill="white", font=font)
        draw.text((width - 16, y + 12), REPORT, fill="#a9bfd6", font=small, anchor="ra")
        y += 52
        figure.paste(frame, (0, y))
        y += frame.height
    figure.save(dest, format="PNG")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("launcher_source", type=Path, help="the helper used for this run")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_frames(args.trace, args.output / "frames.csv")
    write_figure(args.images, args.output / "gate-sample.png")
    source = args.launcher_source.read_text(encoding="utf-8-sig")
    block = source.split("const wchar_t* settings[] = {", 1)[1].split("};", 1)[0]
    profile = dict(v.split("=", 1) for v in re.findall(r'L"(VICTORY_[^"]+)"', block))
    if profile.get("VICTORY_BVH_BUILDER") != "1" or profile.get("VICTORY_THIN_THREADS") != "8":
        raise ValueError("unexpected launcher settings")
    settings = {"report_id": REPORT, "console": "series-x", "environment": profile}
    (args.output / "profile.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
