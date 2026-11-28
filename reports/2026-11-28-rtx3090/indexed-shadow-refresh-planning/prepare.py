"""Generate a standalone benchmark from the actual renderer planner and its reference."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("checkout", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
src = args.checkout / "crates/victory-gpu/src"
host = (src / "host.rs").read_text(encoding="utf8")

def item(prefix):
    start = host.index(prefix)
    return host[start:host.index("\n}", start) + 2]

parts = [
    host[host.index("pub(crate) type ByCopy"):host.index(";", host.index("pub(crate) type ByCopy")) + 1],
    "#[derive(Default)] struct AddressHash(u64);",
    item("impl std::hash::Hasher for AddressHash"),
    "#[derive(Clone,Copy)] " + item("enum Touch {"),
    item("fn front_spans(steps:"),
    "mod indexed {" + (src / "host/front_ranges.rs").read_text(encoding="utf8") + "}",
    Path(__file__).with_name("measure.rs").read_text(encoding="utf8"),
]
args.output.write_text("\n".join(parts), encoding="utf8")
