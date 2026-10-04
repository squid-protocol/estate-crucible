#!/usr/bin/env python3
"""Compile every COBOL program of the estate with GnuCOBOL (`cobc -c -std=ibm`). Stdlib only.

Each program's compile status is part of the answer key (key/manifest.json):
  compiled           compiled as written
  compiled-stubbed   compiled after EXEC SQL / EXEC CICS are replaced by CONTINUE and
                     EXEC SQL INCLUDE by COPY (the precompiler's job, not checked here)
  ibm-only           not compiled as written; `reason` says why. With `check_variant`,
                     a variant with the one IBM-only construct normalised IS compiled,
                     so the rest of the member is still checked.

Copybooks resolve in SYSLIB order: the app's copybook and dclgen libraries, then
shared/copylib, then tools/stubs/ (stand-ins for SQLCA, DFHAID and DFHEIBLK). Lines keep
their numbers through the stubbing, so a cobc message points at the real member line.

    python3 tools/compile.py                   # cobc on PATH, else Docker
    GNUCOBOL_IMAGE=gitgalaxy-gnucobol:3 python3 tools/compile.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ESTATE = ROOT / "estate"
STUBS = ROOT / "tools" / "stubs"
COMMENT = "      *"

_EXEC = re.compile(r"\bEXEC\s+(SQL|CICS)\b", re.I)
_END = re.compile(r"\bEND-EXEC\b", re.I)
_INCLUDE = re.compile(r"\bEXEC\s+SQL\s+INCLUDE\s+([A-Z0-9#@$-]+)\s+END-EXEC", re.I)


def _code(line: str) -> str:
    return line[7:72] if len(line) > 7 else ""


def stub(text: str, *, cics: bool) -> str:
    """Do the precompilers' job crudely, keeping every line where it is."""
    lines = text.split("\n")
    out: list[str] = []
    in_proc = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) > 6 and line[6] in "*/":
            out.append(line)
            i += 1
            continue
        code = _code(line)
        if re.search(r"\bPROCEDURE\s+DIVISION\b", code, re.I):
            in_proc = True
        inc = _INCLUDE.search(code)
        if inc:
            out.append(line[:7] + code[: inc.start()] + f"COPY {inc.group(1)}" + code[inc.end():])
            i += 1
            continue
        m = _EXEC.search(code)
        if not m:
            if cics and re.match(r"\s*WORKING-STORAGE\s+SECTION\.\s*$", code, re.I):
                line = line[:7] + code.rstrip() + " COPY DFHEIBLK."
            out.append(line)
            i += 1
            continue
        prefix = code[: m.start()]
        j = i
        while not _END.search(_code(lines[j]) if j > i else code[m.end():]):
            j += 1
        tail = _code(lines[j]) if j > i else code[m.end():]
        end = _END.search(tail)
        assert end is not None
        suffix = tail[end.end():]
        if in_proc:
            first = line[:7] + prefix + "CONTINUE"
            if j == i:
                out.append(first + suffix)
            else:
                out.append(first)
                out.extend([COMMENT] * (j - i - 1))
                out.append(line[:7] + " " * 4 + suffix.strip() if suffix.strip() else COMMENT)
        else:
            out.extend([COMMENT] * (j - i + 1))
        i = j + 1
    return "\n".join(out)


def variant(text: str, kind: str) -> str:
    if kind == "program-id-period":
        return re.sub(r"^(.{7})PROGRAM-ID\.?\s+([A-Z0-9-]+)\.?[ \t]*$", r"\1PROGRAM-ID. \2.", text, count=1,
                      flags=re.M)
    raise ValueError(kind)


def main(argv: list[str]) -> int:
    manifest = json.loads((ROOT / "key" / "manifest.json").read_text(encoding="utf-8"))
    image = os.environ.get("GNUCOBOL_IMAGE", "gitgalaxy-gnucobol:3")
    use_docker = shutil.which("cobc") is None
    if use_docker and shutil.which("docker") is None:
        print("neither cobc nor docker is available; skipping the compile check")
        return 0
    only = set(argv)
    jobs = []
    with tempfile.TemporaryDirectory(prefix="estate-cobc-") as tmp:
        work = Path(tmp)
        for path, meta in sorted(manifest["members"].items()):
            if meta["library"] != "cobol" or (only and path not in only):
                continue
            status = meta["compile"]["status"]
            check = meta["compile"].get("check_variant")
            if status == "ibm-only" and not check:
                print(f"{path}: not compiled (ibm-only: {meta['compile']['reason']})")
                continue
            name = Path(path).stem
            d = work / name
            d.mkdir()
            app = meta["app"]
            libs = [ESTATE / "apps" / app / "copybook", ESTATE / "apps" / app / "dclgen", ESTATE / "shared" / "copylib",
                    STUBS]
            cics = "EXEC CICS" in (ESTATE / path).read_text(encoding="utf-8").upper()
            for lib in reversed(libs):  # earlier libraries win
                for cb in sorted(lib.glob("*.*")) if lib.is_dir() else []:
                    if cb.suffix in (".cpy", ".dcl"):
                        (d / f"{cb.stem}.cpy").write_text(stub(cb.read_text(encoding="utf-8"), cics=False),
                                                          encoding="utf-8")
            src = (ESTATE / path).read_text(encoding="utf-8")
            if status == "compiled-stubbed":
                src = stub(src, cics=cics)
            if status == "ibm-only":
                src = variant(src, check)
            (d / f"{name}.cbl").write_text(src, encoding="utf-8")
            jobs.append((path, status, name))
        failed = 0
        for path, status, name in jobs:
            cmd = ["cobc", "-c", "-std=ibm", "-I", ".", "-o", f"{name}.o", f"{name}.cbl"]
            if use_docker:
                cmd = ["docker", "run", "--rm", "-v", f"{work / name}:/work", "-w", "/work", image] + cmd
            r = subprocess.run(cmd, cwd=work / name, capture_output=True, text=True, check=False)
            how = {"compiled": "as written", "compiled-stubbed": "EXEC blocks stubbed",
                   "ibm-only": "variant: " + str(manifest["members"][path]["compile"].get("check_variant"))}[status]
            if r.returncode != 0:
                failed += 1
                print(f"{path}: FAILED ({how})\n{r.stdout}{r.stderr}")
            else:
                warn = r.stderr.strip()
                print(f"{path}: ok ({how})" + (f"\n{warn}" if warn else ""))
    print("compile check: " + (f"all {len(jobs)} compiled" if not failed else f"{failed} of {len(jobs)} failed"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
