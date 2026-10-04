"""Writing members in the code page and record format they would have after export.

A member is generated as text lines. `encode` turns them into the exact bytes committed:

  storage lf    lines ending in LF, in a Python codec (utf-8, utf-8-sig, shift_jis): a member
                transferred in text mode, or written on a PC
  storage nel   raw EBCDIC, each line ending in NEL (X'15'): z/OS UNIX text, or a text
                transfer that kept EBCDIC
  storage fb80  raw EBCDIC fixed-block records, 80 bytes each, blank-padded, no line ends:
                a PDS member transferred in binary

EBCDIC tables live in generator/codepages/<page>.json, built from GNU libc iconv by
tools/gen_codepages.py (GitGalaxy's tables come from the JDK, so the two implementations meet
in the scorer). The mixed pages cp930 / cp939 write DBCS runs between Shift-Out (X'0E') and
Shift-In (X'0F'), balanced on every record. Two private-use characters write a raw shift byte
where a horror needs an unbalanced or nested one: U+E00E -> X'0E', U+E00F -> X'0F'.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

HERE = Path(__file__).resolve().parent / "codepages"
EBCDIC_PAGES = ("cp037", "cp273", "cp277", "cp420", "cp930", "cp939")
DBCS_PAGES = ("cp930", "cp939")
SO, SI, NEL, SPACE = 0x0E, 0x0F, 0x15, 0x40
RAW_SO, RAW_SI = "", ""


@cache
def table(page: str) -> tuple[dict[str, int], dict[str, bytes], list]:
    """(char -> single byte, char -> DBCS pair, byte -> char) for an EBCDIC page."""
    doc = json.loads((HERE / f"{page}.json").read_text(encoding="utf-8"))
    sbcs = doc["sbcs"]
    enc = {}
    for b, ch in enumerate(sbcs):
        if ch is not None and ch not in enc and b not in (SO, SI):
            enc[ch] = b
    pairs = {ch: bytes.fromhex(h) for ch, h in doc.get("dbcs", {}).items()}
    return enc, pairs, sbcs


def encode_line(line: str, page: str) -> bytes:
    enc, pairs, _ = table(page)
    out = bytearray()
    shifted = False
    raw = False
    for ch in line:
        if ch == RAW_SO:
            out.append(SO)
            shifted, raw = True, True
            continue
        if ch == RAW_SI:
            out.append(SI)
            shifted = False
            continue
        if ch in enc:
            if shifted:
                out.append(SI)
                shifted = False
            out.append(enc[ch])
        elif ch in pairs:
            if not shifted:
                out.append(SO)
                shifted = True
            out += pairs[ch]
        else:
            raise ValueError(f"{ch!r} (U+{ord(ch):04X}) has no {page} encoding; add it and run tools/gen_codepages.py")
    if shifted and not raw:
        out.append(SI)
    return bytes(out)


def encode(lines: list[str], encoding: str, storage: str, *, check_cols: int = 0) -> bytes:
    """The member's bytes. `check_cols` > 0 asserts every line's code (cols 1-72) fits in that
    many bytes under the member's own encoding (a fixed-format COBOL line must not straddle
    col 72 whichever way a reader counts)."""
    if storage == "lf":
        data = "".join(line + "\n" for line in lines).encode(encoding)
        if check_cols:
            base = encoding.replace("-sig", "")
            for i, line in enumerate(lines, 1):
                if not line.isascii() and len(line.rstrip().encode(base)) > check_cols:
                    raise ValueError(f"line {i}: {len(line.rstrip().encode(base))} bytes in {base}, past col {check_cols}")
        return data
    if encoding not in EBCDIC_PAGES:
        raise ValueError(f"storage {storage} needs an EBCDIC page, not {encoding}")
    recs = [encode_line(line, encoding) for line in lines]
    if check_cols:
        for i, (line, r) in enumerate(zip(lines, recs), 1):  # noqa: B905 -- equal lengths; 3.9
            if not line.isascii() and len(r.rstrip(bytes([SPACE]))) > check_cols:
                raise ValueError(f"record {i}: {len(r)} bytes in {encoding}, past col {check_cols}")
    if storage == "nel":
        return b"".join(r + bytes([NEL]) for r in recs)
    if storage == "fb80":
        out = bytearray()
        for i, r in enumerate(recs, 1):
            if len(r) > 80:
                raise ValueError(f"record {i} is {len(r)} bytes, past 80")
            out += r + bytes([SPACE]) * (80 - len(r))
        return bytes(out)
    raise ValueError(storage)


def decode(data: bytes, encoding: str, storage: str) -> list[str]:
    """The lines back from the bytes (for the compile check and tools/view.py), shift codes
    dropped, a raw shift kept as the private-use character that wrote it."""
    if storage == "lf":
        return data.decode(encoding).split("\n")[:-1]
    recs = [data[i:i + 80] for i in range(0, len(data), 80)] if storage == "fb80" else data.split(bytes([NEL]))[:-1]
    _, pairs, sbcs = table(encoding)
    rev = {v: k for k, v in pairs.items()}
    lines = []
    for r in recs:
        out, i, shifted = [], 0, False
        while i < len(r):
            b = r[i]
            if b == SO:
                shifted, i = True, i + 1
                continue
            if b == SI:
                shifted, i = False, i + 1
                continue
            if shifted and i + 1 < len(r):
                out.append(rev.get(r[i:i + 2], "�"))
                i += 2
                continue
            out.append(sbcs[b] if sbcs[b] is not None else "�")
            i += 1
        text = "".join(out)
        lines.append(text.rstrip(" ") if storage == "fb80" else text)
    return lines
