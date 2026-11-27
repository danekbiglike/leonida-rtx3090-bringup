"""Compile the renderer's exact range selectors and check against per-piece binary search."""

from pathlib import Path
import subprocess
import sys
import tempfile


def main(source, rustc):
    text = source.read_text(encoding="utf8")
    start = text.index("fn flagged_pieces(")
    end = text.index("/// Whether compares read only", start)
    harness = Path(__file__).with_name("harness.rs").read_text(encoding="utf8")
    with tempfile.TemporaryDirectory() as name:
        directory = Path(name)
        code, exe = directory / "range.rs", directory / "range.exe"
        code.write_text(text[start:end] + harness, encoding="utf8")
        subprocess.run([rustc, "--edition=2024", "-Copt-level=3", "-Ctarget-cpu=native",
                        str(code), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
