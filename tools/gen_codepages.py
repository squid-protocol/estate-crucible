#!/usr/bin/env python3
"""Build generator/codepages/*.json from GNU libc iconv. Run once per new code page or new
DBCS characters; the tables are committed data, so the generator itself stays stdlib-only.

    python3 tools/gen_codepages.py

Single-byte pages: every byte 0x00-0xFF decoded one at a time (cp037 and cp273 are also
checked against Python's own codecs). Mixed single/double-byte pages (cp930, cp939): the
single-byte half the same way, and each character above U+00FF that generator/apps/ write
encoded as SO + pair + SI. The tables come from glibc on purpose: GitGalaxy's own EBCDIC tables
were generated from the JDK, so the crucible encodes with an independent implementation.
"""

from __future__ import annotations

import codecs
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "generator" / "codepages"
SBCS = {"cp037": "IBM037", "cp273": "IBM273", "cp277": "IBM277", "cp420": "IBM420"}
DBCS = {"cp930": "IBM930", "cp939": "IBM939"}


def iconv(data: bytes, src: str, dst: str) -> bytes | None:
    r = subprocess.run(["iconv", "-f", src, "-t", dst], input=data, capture_output=True, check=False)
    return r.stdout if r.returncode == 0 else None


def single_bytes(page: str, skip: tuple[int, ...] = ()) -> list:
    table: list = []
    for b in range(256):
        out = None if b in skip else iconv(bytes([b]), page, "UTF-8")
        table.append(out.decode("utf-8") if out and len(out.decode("utf-8")) == 1 else None)
    return table


def main() -> int:
    for name, page in SBCS.items():
        table = single_bytes(page)
        try:
            ref = codecs.lookup(name)
        except LookupError:
            ref = None
        if ref is not None:
            for b, ch in enumerate(table):
                mine = bytes([b]).decode(name)
                if ch is not None and ch != mine:
                    print(f"{name} 0x{b:02X}: iconv {ch!r} python {mine!r}")
        (OUT / f"{name}.json").write_text(json.dumps({"page": name, "source": f"glibc iconv {page}", "sbcs": table},
                                                     ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    # the DBCS repertoire: every character above U+00FF the apps write (plus the ideographic space)
    used = set("\u3000")
    for src in sorted((ROOT / "generator" / "apps").glob("*.py")):
        used |= {ch for ch in src.read_text(encoding="utf-8") if ord(ch) > 0xFF and not 0xE000 <= ord(ch) <= 0xF8FF}
    repertoire = sorted(used)
    for name, page in DBCS.items():
        table = single_bytes(page, skip=(0x0E, 0x0F))
        pairs = {}
        for ch in repertoire:
            out = iconv(ch.encode("utf-8"), "UTF-8", page)
            if out is None:
                continue
            if len(out) == 4 and out[0] == 0x0E and out[3] == 0x0F:
                pairs[ch] = out[1:3].hex().upper()
        missing = [c for c in repertoire if c not in pairs and c not in table]
        if missing:
            print(f"{name}: not encodable: {''.join(missing)}")
        (OUT / f"{name}.json").write_text(json.dumps({"page": name, "source": f"glibc iconv {page}", "sbcs": table,
                                                      "dbcs": pairs}, ensure_ascii=False, indent=0) + "\n",
                                          encoding="utf-8")
    print(f"wrote {len(SBCS) + len(DBCS)} tables to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
