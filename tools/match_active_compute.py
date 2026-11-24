"""Match the first compute container bound in a local VIctory run to a Leonida translation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import blake3


def first_compute(path):
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    pattern = re.compile(r'first bind\b.*?stage="compute"\s+size=(\d+)\s+hash=([0-9a-f]{16})\b')
    with path.open(encoding="utf-8", errors="replace") as log:
        for line in log:
            match = pattern.search(ansi.sub("", line))
            if match:
                return int(match[1]), match[2]
    raise ValueError("The trace contains no first bind of a compute pipeline.")


def match_program(args):
    size, prefix = first_compute(args.victory_log)
    matches = [path for path in args.dxbc.glob("*.dxbc")
               if path.stat().st_size == size and blake3.blake3(path.read_bytes()).hexdigest().startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"The size and recorded hash prefix match {len(matches)} containers. A unique match is required.")
    name = matches[0].stem
    meta = json.loads((args.translated / "index.json").read_bytes()).get(name, {})
    source = (args.dxbc / "fssm" / (name + ".fssm")).read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if meta.get("stage") != "cs" or digest != meta.get("fssm_sha256"):
        raise ValueError("The translated entry and compute source disagree.")
    with args.leonida_log.open(encoding="utf-8", errors="replace") as log:
        if not any("] compute-request " in line and f" code={digest} state=-" in line for line in log):
            raise ValueError("The observed Leonida run did not request this compute source.")
    subprocess.run([args.validator, "--target-env", "vulkan1.3", str(args.translated / (name + ".spv"))], check=True)
    return name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("victory-log", "leonida-log", "dxbc", "translated"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--validator", default="spirv-val")
    try:
        print(match_program(parser.parse_args()))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
