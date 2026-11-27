"""Build a standalone microbenchmark from the two actual renderer implementations."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
repo = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else root / "nvidia-paired"
draw = "crates/victory-gpu/src/draw.rs"
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
baseline = "bf8f3dc0b8cc71458f227b60486f8f88557255dd"
flat = subprocess.check_output(["git", "-C", str(repo), "show", baseline + ":" + draw]).decode()
current = (repo / draw).read_text(encoding="utf-8")
for name, source in [("flat", flat), ("striped", current)]:
    constant = re.search(r"const HEAP_ROUND: u64 = \d+;", source)[0]
    layout = source[source.index("struct HeapRanges<T>"):source.index("/// Descriptor-derived references")]
    methods = source[source.index("impl<T> HeapRanges<T> {"):source.index("#[cfg(test)]\nmod heap_range_tests")]
    layout = layout.replace("struct HeapRanges<T>", "pub(super) struct HeapRanges<T>")
    methods = methods.replace("    fn set(", "    pub(super) fn set(")
    methods = methods.replace("    fn ranges(", "    pub(super) fn ranges(")
    args = "p, HEAP_ROUND as u32" if name == "flat" else "p"
    wrapper = f"pub(super) fn forget(r: &mut HeapRanges<u32>, p: u32) {{ r.forget_part({args}); }}"
    (out / (name + ".rs")).write_text("\n".join([constant, layout, methods, wrapper]), encoding="utf-8")
shutil.copyfile(root / "stripe-bench.rs", out / "main.rs")
