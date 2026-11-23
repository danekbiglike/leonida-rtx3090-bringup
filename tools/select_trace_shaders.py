"""Stage local shader assembly requested by a Leonida trace for rdna2spirv."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile


MISSING = re.compile(rb"no translated \w+ (?:shader )?for FSSM sha256 ([0-9a-f]{64})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxbc", type=Path, help="existing DXBC folder with fssm and disasm subfolders")
    parser.add_argument("traces", nargs="+", type=Path, help="runtime.log files from local startup runs")
    parser.add_argument("--check", action="store_true", help="report coverage without staging any files")
    args = parser.parse_args()
    dxbc = args.dxbc.resolve()
    if not all((dxbc / name).is_dir() for name in ("fssm", "disasm")):
        parser.error("run the shader carve and disassembly stages first")
    requested = set()
    for trace in args.traces:
        with trace.open("rb") as stream:
            for line in stream:
                match = MISSING.search(line)
                if match:
                    requested.add(match[1].decode("ascii"))
    if not requested:
        parser.error("no missing FSSM programs found in the supplied traces")

    selected = {}
    for blob in sorted((dxbc / "fssm").glob("*.fssm")):
        with blob.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest in requested and digest not in selected:
            source = dxbc / "disasm" / blob.with_suffix(".s").name
            if source.is_file():
                selected[digest] = source
        if len(selected) == len(requested):
            break
    print(f"Requested {len(requested)}. Matched with assembly {len(selected)}. "
          f"Unmatched {len(requested) - len(selected)}.")
    if args.check:
        return
    if not selected:
        parser.error("none of the requested programs have matching assembly here")
    # The translator resolves sidecars relative to the parent of its assembly folder.
    stage = Path(tempfile.mkdtemp(prefix="trace-disasm-", dir=dxbc))
    for source in selected.values():
        try:
            os.link(source, stage / source.name)
        except OSError:
            shutil.copyfile(source, stage / source.name)
    print(stage)


if __name__ == "__main__":
    main()
