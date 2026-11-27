"""Assemble a standalone Rust bench from the two renderer source trees."""
import re
import sys
from pathlib import Path


def section(text, start, stop):
    first = text.index(start)
    return text[first:text.index(stop, first)]


def planner(text, name):
    body = section(text, "fn plan(does:", "/// Whether a refresh of `does`")
    return body.replace("fn plan(", f"#[inline(never)]\nfn {name}(", 1)


baseline, patched, output = map(Path, sys.argv[1:])
relative = Path("crates/victory-gpu/src")
files = [p / relative / "host/card_steps.rs" for p in (baseline, patched)]
before, after = [p.read_text(encoding="utf8") for p in files]
host = (baseline / relative / "host.rs").read_text(encoding="utf8")
parts = [
    "#![allow(dead_code)]",
    *re.findall(r"^const (?:MOST|BEHIND_PLACED):.+?;$", before, re.M),
    section(host, "fn touches(ranges:", "/// Whether anything is in the air."),
    section(before, "#[derive(Clone, Copy, Debug, PartialEq, Eq)]\nenum Does", "/// The steps of `does`"),
    planner(before, "baseline"),
    planner(after, "fast"),
    Path(__file__).with_name("harness.rs").read_text(encoding="utf8"),
]
output.write_text("\n".join(parts), encoding="utf8")
