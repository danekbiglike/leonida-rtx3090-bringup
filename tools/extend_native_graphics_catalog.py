"""Extend a local shader catalogue with the most requested missing fragment programs."""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def read_index(directory):
    return json.loads((directory / "index.json").read_bytes())


def requested_pairs(log, native):
    counts = collections.Counter()
    first = {}
    with log.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = re.search(r"native-request=(\d+) hr=([0-9a-f]+)(.*)", line)
            if not match or int(match[2], 16) != 0x80004001:
                continue
            stages = []
            for block in re.findall(r"\[([^\]]*)\]", match[3]):
                refs = {(native[key][0], Path(native[key][1]).stem) for key in block.split() if key in native}
                if len(refs) != 1:
                    break
                stages.append(refs.pop())
            else:
                if sorted(stage for stage, _ in stages) == ["ps", "vs"]:
                    pair = tuple(dict(stages)[stage] for stage in ("vs", "ps"))
                    counts[pair] += 1
                    first[pair] = min(int(match[1]), first.get(pair, int(match[1])))
    return sorted(counts, key=lambda p: (-counts[p], first[p])), counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("leonida", "dxbc", "translated", "preferred", "base", "log", "output"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--validator", required=True, help="Path to spirv-val.")
    parser.add_argument("--count", type=int, default=2)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir() or args.count < 1:
        parser.error("Choose a new catalogue directory inside an existing parent and a positive count.")
    if args.base.resolve() in args.output.resolve().parents:
        parser.error("Place the new catalogue outside its source.")
    spec = importlib.util.spec_from_file_location("native_hash_tool", args.leonida / "tools/native_pso_hashes.py")
    hash_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hash_tool)
    native = hash_tool.build(str(args.dxbc), str(args.translated))
    pairs, counts = requested_pairs(args.log, native)
    base = read_index(args.base)
    preferred = read_index(args.preferred)
    extras = {}
    for vs, ps in pairs:
        if vs not in base or ps in base or ps in extras or ps not in preferred:
            continue
        meta = preferred[ps]
        if meta.get("stage") != "ps" or not meta.get("wave64_emulated") or meta.get("wave64_graphics") != "A":
            continue
        module = args.preferred / (ps + ".spv")
        if not module.is_file() or module.resolve().parent != args.preferred.resolve():
            continue
        subprocess.run([args.validator, "--target-env", "vulkan1.3", str(module)], check=True)
        extras[ps] = module
        print(f"Matched {counts[vs, ps]} requests for {ps}")
        if len(extras) == args.count:
            break
    if len(extras) != args.count:
        parser.error(f"Found {len(extras)} matching additions. Choose a lower count or collect a new trace.")
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temp:
        dest = Path(temp) / "catalog"
        shutil.copytree(args.base, dest)
        for name, module in extras.items():
            shutil.copyfile(module, dest / module.name)
            base[name] = preferred[name]
        (dest / "index.json").write_text(json.dumps(base, ensure_ascii=True), encoding="utf-8")
        # Build paths relative to the final folder. The table is written in the staging folder first.
        table = hash_tool.build(str(args.dxbc), str(dest))
        adjusted = {}
        for key, (stage, relative) in table.items():
            source = (dest / relative).resolve()
            final_path = os.path.relpath(source, args.output.resolve()).replace(os.sep, "/")
            adjusted[key] = (stage, final_path)
        hash_tool.write(str(dest), adjusted)
        dest.rename(args.output)
    print(f"Wrote {len(extras)} additional modules and {len(base)} main-index entries.")


if __name__ == "__main__":
    main()
