"""Extract texture queue code for the standalone benchmark from two source files."""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("Usage: python extract.py ORIGINAL_HOST_RS PATCHED_HOST_RS")
for label, argument in zip(("before", "after"), sys.argv[1:]):
    body = Path(argument).read_text(encoding="utf-8")
    first = body.index("struct Waiting {")
    last = body.index("/// Whether `view` is of", first)
    Path(__file__).with_name(label + ".rs").write_text(body[first:last], encoding="utf-8")
