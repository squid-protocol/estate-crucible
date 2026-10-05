#!/usr/bin/env python3
"""Compile every COBOL program of the estate with GnuCOBOL (`cobc -c -std=ibm`). Stdlib only.

Each program's compile status is part of the answer key (key/manifest.json):
  compiled           compiled as written
  compiled-stubbed   compiled after EXEC SQL / EXEC CICS are replaced by CONTINUE and
                     EXEC SQL INCLUDE by COPY (the precompiler's job, not checked here)
  ibm-only           not compiled as written; `reason` says why. With `check_variant`,
                     a variant with the one IBM-only construct normalised IS compiled,
                     so the rest of the member is still checked.

Copybooks resolve in the member's SYSLIB order from key/manifest.json `copy_libraries` (by
default the app's copybook and dclgen libraries, then shared/copylib), then tools/stubs/
(stand-ins for SQLCA, DFHAID and DFHEIBLK). Lines keep their numbers through the stubbing,
so a cobc message points at the real member line.

    python3 tools/compile.py                   # cobc on PATH, else Docker
    GNUCOBOL_IMAGE=gitgalaxy-gnucobol:3 python3 tools/compile.py
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from generator.codepages import decode  # noqa: E402
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


def to_free(text: str) -> str:
    """Fixed format -> free format for cobc -free: a member with multi-byte characters is
    longer in UTF-8 than in its own code page, so its columns would not survive the decode.
    Cols 1-6 go, a col-7 comment becomes *>, cols 73-80 go."""
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith(">>"):
            out.append(line.strip())
        elif len(line) > 6 and line[6] in "*/":
            out.append("*>" + line[7:])
        else:
            out.append(line[7:72] if line.isascii() else line[7:])
    return "\n".join(out)


def stand_in(text: str, include: Path) -> str:
    """An `incomplete` member COPYs a member the estate lacks (a gap): stand a one-byte FILLER
    in for each such COPY, so the rest of the member is still compiled."""

    def sub(m: "re.Match[str]") -> str:
        name = m.group(1)
        return m.group(0) if (include / f"{name}.cpy").exists() else "05 FILLER PIC X."

    return re.sub(r"\bCOPY\s+([A-Z0-9#@$-]+)\s*\.", sub, text)


def variant(text: str, kind: str) -> str:
    if kind == "pic-g-to-n":
        return re.sub(r"\bG'", "N'", re.sub(r"(PIC\s+)G\(", r"\1N(", text))
    if kind == "u3000-to-space":
        return text.replace("\u3000", " ")
    if kind == "program-id-period":
        return re.sub(r"^(.{7})PROGRAM-ID\.?\s+([A-Z0-9-]+)\.?[ \t]*$", r"\1PROGRAM-ID. \2.", text, count=1,
                      flags=re.M)
    raise ValueError(kind)


MANIFEST: dict = {}


def text_of(p: Path) -> str:
    """A member as text: decoded from its code page and record format (key/manifest.json)."""
    if ESTATE not in p.parents:  # tools/stubs: plain text
        return p.read_text(encoding="utf-8")
    meta = MANIFEST["members"][str(p.relative_to(ESTATE)).replace("\\", "/")]
    return "".join(line + "\n" for line in decode(p.read_bytes(), meta["encoding"], meta["storage"]))


def main(argv: list[str]) -> int:
    manifest = json.loads((ROOT / "key" / "manifest.json").read_text(encoding="utf-8"))
    MANIFEST.update(manifest)
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
            if only and path not in only:
                continue
            if meta["library"] == "pli":
                print(f"{path}: not compiled (ibm-only: {meta['compile']['reason']})")
                continue
            if meta["library"] != "cobol":
                continue
            status = meta["compile"]["status"]
            check = meta["compile"].get("check_variant")
            if status in ("ibm-only", "other-dialect", "incomplete") and not check:
                print(f"{path}: not compiled (ibm-only: {meta['compile']['reason']})")
                continue
            name = Path(path).stem
            d = work / name
            d.mkdir()
            # the member's SYSLIB order, from the key's copy-library declaration
            decl = manifest["copy_libraries"]
            order = next((r["order"] for r in decl["syslib"] if fnmatch.fnmatchcase(path, r["programs"])), ["SHRCPY"])
            libs = [ESTATE / d for n in order for d in decl["libraries"].get(n, [])] + [STUBS]
            cics = "EXEC CICS" in text_of(ESTATE / path).upper()
            lib_names = [n for n in order for _d in decl["libraries"].get(n, [])] + [None]
            # `COPY member IN library` may name a library outside the order
            for n, dirs in decl["libraries"].items():
                if n not in order:
                    libs.append(ESTATE / dirs[0])
                    lib_names.append(n + "*")
            for lib, lib_name in reversed(list(zip(libs, lib_names))):  # noqa: B905 -- earlier libraries win
                for cb in sorted(lib.glob("*.*")) if lib.is_dir() else []:
                    if cb.suffix in (".cpy", ".dcl"):
                        text = stub(text_of(cb), cics=False)
                        if lib_name and lib_name.endswith("*"):  # only reachable by IN library
                            lib_name = lib_name[:-1]
                        else:
                            (d / f"{cb.stem}.cpy").write_text(text, encoding="utf-8")
                        if lib_name:  # `COPY member IN library` reads <library>/<member>
                            (d / lib_name).mkdir(exist_ok=True)
                            (d / lib_name / f"{cb.stem}.cpy").write_text(text, encoding="utf-8")
            src = text_of(ESTATE / path)
            if status in ("compiled-stubbed", "incomplete"):
                src = stub(src, cics=cics)
            if status == "incomplete":
                src = stand_in(src, d)
            if status in ("ibm-only", "other-dialect"):
                src = variant(src, check)
                for cpy in [*d.glob("*.cpy"), *d.glob("*/*.cpy")]:
                    cpy.write_text(variant(cpy.read_text(encoding="utf-8"), check), encoding="utf-8")
            free = "\n       >>SOURCE FORMAT FREE" in "\n" + src or not src.isascii()
            if free and not src.lstrip().startswith(">>SOURCE"):
                src = to_free(src)
                for cpy in d.glob("*.cpy"):
                    t = cpy.read_text(encoding="utf-8")
                    cpy.write_text(to_free(t), encoding="utf-8")
                for cpy in d.glob("*/*.cpy"):
                    cpy.write_text(to_free(cpy.read_text(encoding="utf-8")), encoding="utf-8")
            (d / f"{name}.cbl").write_text(src, encoding="utf-8")
            jobs.append((path, status, name, free and not src.lstrip().startswith(">>SOURCE")))
        failed = 0
        for path, status, name, free in jobs:
            cmd = ["cobc", "-c", "-std=ibm", *(["-free"] if free else []), "-I", ".", "-o", f"{name}.o", f"{name}.cbl"]
            if use_docker:
                cmd = ["docker", "run", "--rm", "-v", f"{work / name}:/work", "-w", "/work", image] + cmd
            r = subprocess.run(cmd, cwd=work / name, capture_output=True, text=True, check=False)
            how = {"compiled": "as written", "compiled-stubbed": "EXEC blocks stubbed",
                   "incomplete": "missing members stood in, EXEC blocks stubbed",
                   "ibm-only": "variant: " + str(manifest["members"][path]["compile"].get("check_variant")),
                   "other-dialect": "variant: " + str(manifest["members"][path]["compile"].get("check_variant"))}[status]
            if free:
                how += ", decoded to UTF-8 and compiled as free format"
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
