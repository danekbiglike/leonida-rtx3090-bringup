"""Add SPIR-V-validated vertex and pixel stages for a 32-lane PC GPU to a local graphics catalogue."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from uuid import uuid4


def prepare(args):
    full = args.translated.resolve()
    base = args.base.resolve()
    output = args.output.resolve()
    for source in (base, full, args.dxbc.resolve()):
        if output == source or source in output.parents:
            raise ValueError("Choose a new output directory outside the inputs.")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("The output must be new and its parent must exist.")
    validator = shutil.which(args.validator)
    if not validator:
        raise ValueError("spirv-val was not found.")
    index = json.loads((base / "index.json").read_bytes())
    source_index = json.loads((full / "index.json").read_bytes())
    candidates = {
        name: meta for name, meta in source_index.items()
        if name not in index and meta.get("stage") in ("vs", "ps")
        and (meta.get("subgroup_size") == 32 or meta.get("wave64_graphics") in ("A", "B"))
    }

    def validate(name):
        module = full / (name + ".spv")
        if module.parent != full or not module.is_file():
            return name, None, "missing"
        checked = subprocess.run([validator, "--target-env", "vulkan1.3", str(module)], capture_output=True)
        return (name, module, "valid") if checked.returncode == 0 else (name, None, "rejected")

    spec = importlib.util.spec_from_file_location("native_pso_hashes", args.leonida / "tools/native_pso_hashes.py")
    hashes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hashes)
    # A normal sibling inherits the same read permissions as the final folder, including on Windows.
    working = output.parent / (".draw-catalog-" + uuid4().hex)
    working.mkdir()
    counts = Counter()
    try:
        shutil.copytree(base, working, dirs_exist_ok=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            for name, module, status in pool.map(validate, candidates):
                counts[status] += 1
                if module:
                    shutil.copyfile(module, working / module.name)
                    index[name] = candidates[name]
        (working / "index.json").write_text(json.dumps(index, ensure_ascii=True), encoding="utf-8")
        hashes.write(str(working), hashes.build(str(args.dxbc), str(working)))
        working.rename(output)
    finally:
        if working.exists():
            shutil.rmtree(working)
    print(f"{len(index)} main-index entries, {counts['valid']} added, "
          f"{counts['rejected']} rejected by spirv-val, {counts['missing']} missing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("base", "translated", "dxbc", "output", "leonida"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--validator", default="spirv-val")
    prepare(parser.parse_args())
