"""Build the RTX 3090 comparison from the per-scene Present summaries."""
import json
from pathlib import Path

report_dir = Path(__file__).resolve().parents[1] / "reports" / "2026-11-26-rtx3090"
builds = [
    ("paired-wave", "Paired shaders", "paired-waves.md"),
    ("paired-wave-queue", "Separate copy queue", "paired-waves.md"),
    ("paired-wave-pieces", "16 KiB transfers", "paired-wave-pieces.md"),
    ("paired-wave-merge", "Local AVX2 merge", "relay-merge-avx2.md"),
    ("paired-wave-heaps", "Descriptor refresh", "descriptor-refresh.md"),
    ("paired-wave-land", "Parallel copy-back", "parallel-relay.md"),
    ("paired-wave-spans", "Joined readback commands", "join-fetch-ranges.md"),
    ("paired-wave-mips", "Descriptor locks and texture mips", "descriptor-locks-texture-mips.md"),
    ("paired-wave-journal", "Lazy write-watch range preparation", "buffer-refresh-and-hitches.md"),
    ("paired-wave-cardsync", "Small buffers in GPU memory", "small-card-buffers.md"),
    ("paired-wave-shorthash", "Small buffers with shorter GPU hashes", "short-buffer-hashes.md"),
]
scenes = [("window", ""), ("door", "-room"), ("movement", "-moving"), ("additional", "-route")]
rows = []
for stem, name, report in builds:
    samples = {}
    for scene, suffix in scenes:
        path = report_dir / f"{stem}{suffix}-summary.json"
        if not path.is_file():
            continue
        run = json.loads(path.read_text(encoding="utf-8"))
        samples[scene] = {key: run[key] for key in (
            "fps", "p95_ms", "max_ms", "frames", "covered_seconds", "mean_draw_calls", "frames_over_200ms"
        )}
        samples[scene]["source"] = path.name
    if samples:
        rows.append({"build": name, "report": report, "samples": samples})
index = {"gpu": "GeForce RTX 3090", "cpu": "Ryzen 7 3700X", "profile": "Series X",
         "clock": "Intervals between successful DXGI presents", "builds": rows}
(report_dir / "gameplay-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
lines = ["# RTX 3090 gameplay comparison", "",
         "Ryzen 7 3700X with the Series X graphics profile. Values are average FPS. "
         "Each number links to frame times, the 95th percentile and the number of frames over 200 ms. "
         "Movement routes and NPC positions can differ between runs. See each report for screenshots and controls. "
         "[Machine-readable index](gameplay-index.json)", "",
         "| Renderer build | Facing window | Facing door | With movement keys | Additional minute |",
         "| --- | ---: | ---: | ---: | ---: |"]
for row in rows:
    cells = [f"[{row['build']}]({row['report']})"]
    for scene, _ in scenes:
        s = row["samples"].get(scene)
        cells.append(f"[{s['fps']:.2f}]({s['source']})" if s else "—")
    lines.append("| " + " | ".join(cells) + " |")
(report_dir / "gameplay-comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
