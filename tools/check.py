#!/usr/bin/env python3
"""The repository's gate. Stdlib only.

1. Regenerates the estate, key and horror catalog in memory with the committed settings
   (key/manifest.json's generator block) and fails on any difference from the committed
   files -- a hand edit, a stale regeneration, or a generator change that was not re-run.
2. Checks the key's own consistency: every member hash, every horror tag defined and
   cited, every fact on a known channel with its required fields, every line in range.
3. Unless --no-compile, runs tools/compile.py (GnuCOBOL, cobc on PATH or Docker).

    python3 tools/check.py [--no-compile]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from generator import FORMAT  # noqa: E402
from generator.__main__ import GENERATED_DIRS, build  # noqa: E402
from generator.model import CHANNELS  # noqa: E402

REQUIRED = {
    "programs": ("program_id", "line"),
    "units": ("name", "kind", "start_line", "end_line"),
    "edges": ("kind", "from", "target", "line"),
    "call_sites": ("verb", "form", "operand", "line"),
    "copies": ("member", "kind", "line", "resolves_to"),
    "data_items": ("level", "name", "line"),
    "layouts": ("record", "line", "bytes", "fields"),
    "sql_statements": ("verb", "line"),
    "sql_tables": ("table", "line", "columns"),
    "jcl_steps": ("step", "ordinal", "line"),
    "jcl_dds": ("step", "dd", "line"),
    "screen_fields": ("kind", "mapset", "line"),
    "csd_resources": ("type", "name", "group", "line"),
    "transactions": ("transid", "program", "line"),
    "cics_resources": ("verb", "kind", "name", "access", "line"),
    "jcl_datasets": ("dsn", "step", "dd", "line"),
    "file_control": ("select", "assign", "organization", "file_status", "line"),
    "entry_points": ("kind", "program", "params", "line"),
    "file_edges": ("kind", "target"),
}


def regenerated_diff() -> list[str]:
    manifest = json.loads((ROOT / "key" / "manifest.json").read_text(encoding="utf-8"))
    gen = manifest["generator"]
    files = build(gen["size"], gen["seed"])
    problems = []
    committed = {
        str(p.relative_to(ROOT)).replace("\\", "/")
        for d in GENERATED_DIRS
        for p in (ROOT / d).rglob("*")
        if p.is_file()
    }
    for rel, text in sorted(files.items()):
        p = ROOT / rel
        if not p.is_file():
            problems.append(f"{rel}: generated but not committed")
        elif p.read_bytes() != text.encode("utf-8"):
            problems.append(f"{rel}: differs from a regeneration (hand-edited, or the generator changed without "
                            f"`python3 -m generator`)")
    for rel in sorted(committed - set(files)):
        problems.append(f"{rel}: committed but not generated")
    return problems


def key_consistency() -> list[str]:
    problems = []
    manifest = json.loads((ROOT / "key" / "manifest.json").read_text(encoding="utf-8"))
    spec = json.loads((ROOT / "spec" / "horrors.json").read_text(encoding="utf-8"))
    defined = {h["id"]: h for h in spec["horrors"]}
    if manifest["format"] != FORMAT:
        problems.append(f"key/manifest.json: format {manifest['format']} is not {FORMAT}")
    for hid, h in defined.items():
        for field in ("title", "category", "asserts", "citations"):
            if not h.get(field):
                problems.append(f"spec/horrors.json {hid}: no {field}")
        for c in h.get("citations", []):
            if not (c.get("url", "").startswith("https://") and c.get("section") and c.get("quote")):
                problems.append(f"spec/horrors.json {hid}: a citation needs url, section and quote")
    for path, meta in manifest["members"].items():
        src = ROOT / "estate" / path
        if hashlib.sha256(src.read_bytes()).hexdigest() != meta["sha256"]:
            problems.append(f"{path}: sha256 differs from key/manifest.json")
        nlines = src.read_text(encoding="utf-8").count("\n")
        entry = json.loads((ROOT / meta["key"]).read_text(encoding="utf-8"))["members"][path]
        if entry["lines"] != nlines:
            problems.append(f"{path}: key says {entry['lines']} lines, the member has {nlines}")
        for ch in CHANNELS:
            for fact in entry.get(ch, []):
                missing = [f for f in REQUIRED[ch] if f not in fact]
                if missing:
                    problems.append(f"{path} {ch}: fact without {missing}: {fact}")
                for f in ("line", "start_line", "end_line"):
                    if f in fact and not 1 <= fact[f] <= nlines:
                        problems.append(f"{path} {ch}: {f} {fact[f]} outside 1..{nlines}")
                if fact.get("horror") and fact["horror"] not in defined:
                    problems.append(f"{path} {ch}: undefined horror {fact['horror']}")
        for ph in entry.get("phantoms", []):
            if ph["channel"] not in CHANNELS or not ph.get("why"):
                problems.append(f"{path}: malformed phantom {ph}")
    return problems


def main(argv: list[str]) -> int:
    problems = regenerated_diff() + key_consistency()
    for p in problems:
        print(f"FAIL {p}")
    print(f"generated tree and key: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    rc = 1 if problems else 0
    if "--no-compile" not in argv:
        rc |= subprocess.run([sys.executable, str(ROOT / "tools" / "compile.py")], check=False).returncode
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
