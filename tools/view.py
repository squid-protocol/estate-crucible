#!/usr/bin/env python3
"""Print a member as text, whatever its code page: python3 tools/view.py estate/apps/NORD/cobol/KØBREG.cbl

The member's encoding and record format come from key/manifest.json; DBCS shift codes are
dropped. Line numbers are the key's."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from generator.codepages import decode  # noqa: E402


def main(argv: list[str]) -> int:
    manifest = json.loads((ROOT / "key" / "manifest.json").read_text(encoding="utf-8"))
    for arg in argv:
        p = Path(arg).resolve()
        rel = str(p.relative_to(ROOT / "estate")).replace("\\", "/")
        meta = manifest["members"][rel]
        print(f"== {rel}  ({meta['encoding']}, {meta['storage']}, {meta['bytes']} bytes)")
        for n, line in enumerate(decode(p.read_bytes(), meta["encoding"], meta["storage"]), 1):
            print(f"{n:5d}  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
