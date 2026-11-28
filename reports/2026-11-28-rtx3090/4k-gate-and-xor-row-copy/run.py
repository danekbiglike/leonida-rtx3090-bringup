"""Compare the same Series X tiling workloads on a single CPU thread."""
import argparse
import csv
import itertools
import statistics
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rustc", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    name = Path("crates/victory-formats/src/texture.rs")
    args.work.mkdir(parents=True, exist_ok=True)
    rows = []
    binaries = {}
    flags = ["--edition=2024", "-Copt-level=3", "-Ctarget-cpu=native"]
    for label in ("before", "after"):
        folder = args.work.resolve() / label
        source = folder / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((args.baseline / name).read_bytes())
        if label == "after":
            subprocess.run(["git", "apply", "--no-index", str(here / "xor-row-copy.patch")], cwd=folder, check=True)
        test = folder / "format_tests.exe"
        subprocess.run([args.rustc, *flags, "--test", source, "-o", test], check=True)
        result = subprocess.run([test, "--test-threads=1"], check=True, capture_output=True, text=True)
        (here / f"tests-{label}.txt").write_text(result.stdout, encoding="utf-8")
        library = folder / "libbench_texture.rlib"
        subprocess.run([args.rustc, *flags, "--crate-name=bench_texture", "--crate-type=rlib", source, "-o", library], check=True)
        binaries[label] = folder / "measure.exe"
        subprocess.run([args.rustc, *flags, here / "bench_tiling.rs", "--extern", f"bench_texture={library}",
                        "-o", binaries[label]], check=True)
    for run, label in enumerate(("before", "after", "after", "before"), 1):
        result = subprocess.run([binaries[label]], check=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            w, h, n, iteration, tile, detile = map(int, line.split(","))
            rows.append(dict(width=w, height=h, bytes_per_texel=n, variant=label, process_run=run,
                             iteration=iteration, tile_ns=tile, detile_ns=detile))
    with (here / "samples.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    def key(row):
        return (row["width"], row["height"], row["bytes_per_texel"], row["variant"])
    for group, batch in itertools.groupby(sorted(rows, key=key), key=key):
        batch = list(batch)
        print(*group, len(batch), *(round(statistics.median(r[field] for r in batch) / 1000, 2)
                                    for field in ("tile_ns", "detile_ns")), flush=True)


if __name__ == "__main__":
    main()
