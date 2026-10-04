"""python3 -m generator [--out DIR] [--size small|medium|large] [--filler-apps N] [--seed N]

Writes estate/, key/ and horrors/ under --out (default: this repository). The committed
tree is `--size small --seed 1`; `tools/check.py` regenerates it and diffs."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .apps import HAND_APPS
from .apps.filler import filler_apps
from .estate import Estate, write_tree
from .shared import SHARED

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "horrors.json"
GENERATED_DIRS = ("estate", "key", "horrors")

# size preset -> number of seeded filler apps added to the hand-written ones
SIZES = {"small": 0, "medium": 12, "large": 120}
DEFAULT_SEED = 1


def build(size: str = "small", seed: int = DEFAULT_SEED, filler: int | None = None) -> dict[str, str]:
    horrors = json.loads(SPEC.read_text(encoding="utf-8"))["horrors"]
    count = SIZES[size] if filler is None else filler
    estate = Estate(HAND_APPS + filler_apps(seed, count), SHARED, horrors, seed, size)
    estate.build()
    return estate.files()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m generator", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT)
    ap.add_argument("--size", choices=sorted(SIZES), default="small")
    ap.add_argument("--filler-apps", type=int, default=None, help="override the size preset's filler-app count")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args(argv)
    files = build(args.size, args.seed, args.filler_apps)
    for d in GENERATED_DIRS:
        shutil.rmtree(args.out / d, ignore_errors=True)
    write_tree(files, args.out)
    members = sum(1 for p in files if p.startswith("estate/"))
    print(f"wrote {members} members, {len(files) - members} key/catalog files under {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
