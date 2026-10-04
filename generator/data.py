"""DATA DIVISION items: writing them, and the storage each one occupies.

Sizes follow Enterprise COBOL for z/OS, Programming Guide, "Examples: numeric data and
internal representation" and Language Reference, "USAGE clause" (cited per horror and in
SPEC.md): DISPLAY = one byte per character position (S and V take none unless SIGN
SEPARATE); BINARY / COMP / COMP-4 / COMP-5 = 2, 4 or 8 bytes for 1-4, 5-9 or 10-18
digits; PACKED-DECIMAL / COMP-3 = digits // 2 + 1; COMP-1 = 4; COMP-2 = 8.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from .model import Member

Item = dict[str, Any]


def I(lvl: int, name: str, pic: Optional[str] = None, usage: Optional[str] = None, *,  # noqa: E741 -- the DSL's item constructor
      occurs: Optional[int] = None, redefines: Optional[str] = None, value: Optional[str] = None,
      kids: Optional[list[Item]] = None, copy: Optional[list[str]] = None, copy_style: str = "next-line",
      horror: Optional[str] = None) -> Item:
    """One data description entry. `copy` makes it a group whose subordinate entries come
    from COPY members; `copy_style` is how the COPY is written: next-line, same-line
    (`01 X. COPY Y.`, several on one line) or split (`COPY` / member on the next line)."""
    return {"lvl": lvl, "name": name, "pic": pic, "usage": usage, "occurs": occurs, "redefines": redefines,
            "value": value, "kids": kids or [], "copy": copy or [], "copy_style": copy_style, "horror": horror}


def C(member: str, *, horror: Optional[str] = None, style: str = "next-line") -> Item:
    """A bare COPY of a member that holds whole records (01 levels of its own)."""
    return {"copy_only": member, "copy_style": style, "horror": horror}


def SQLINC(member: str) -> Item:
    """EXEC SQL INCLUDE member END-EXEC."""
    return {"sql_include": member}


_PIC_REPEAT = re.compile(r"(.)\((\d+)\)")


def pic_positions(pic: str) -> str:
    """The PICTURE string with every `x(n)` repeat expanded."""
    return _PIC_REPEAT.sub(lambda m: m.group(1) * int(m.group(2)), pic.upper())


def elementary_bytes(pic: str, usage: Optional[str]) -> int:
    expanded = pic_positions(pic)
    u = norm_usage(usage) or "DISPLAY"
    digits = expanded.count("9")
    if u in ("COMP-1",):
        return 4
    if u in ("COMP-2",):
        return 8
    if u in ("COMP", "COMPUTATIONAL", "BINARY", "COMP-4", "COMP-5"):
        return 2 if digits <= 4 else 4 if digits <= 9 else 8
    if u in ("COMP-3", "PACKED-DECIMAL"):
        return digits // 2 + 1
    return sum(1 for ch in expanded if ch not in "SVP")


def norm_usage(usage: Optional[str]) -> Optional[str]:
    """`USAGE COMP` and `COMP` are the same clause; the key records the usage word alone."""
    if not usage:
        return None
    u = usage.upper().strip()
    return u[len("USAGE "):].strip() if u.startswith("USAGE ") else u


def item_clauses(it: Item) -> list[str]:
    parts = []
    if it.get("redefines"):
        parts.append(f"REDEFINES {it['redefines']}")
    if it.get("pic"):
        parts.append(f"PIC {it['pic']}")
    if it.get("usage"):
        parts.append(it["usage"])
    if it.get("occurs"):
        parts.append(f"OCCURS {it['occurs']} TIMES")
    if it.get("value") is not None:
        parts.append(f"VALUE {it['value']}")
    return parts


def item_text(it: Item) -> str:
    head = f"{it['lvl']:02d}  {it['name']}"
    rest = " ".join(item_clauses(it))
    if not rest:
        return head
    # line the PIC up in a column, the way most shops keep a record layout
    return f"{head:<27}{rest}" if len(head) < 27 else f"{head} {rest}"


def _wrap(it: Item, first: int, rest: int) -> list[str]:
    """Split an entry at clause boundaries to fit the line widths: the head and as many
    clauses as fit, then the rest on continuation lines."""
    clauses = item_clauses(it)
    out = [item_text({**it, "redefines": None, "pic": None, "usage": None, "occurs": None, "value": None})]
    for c in clauses:
        width = first if len(out) == 1 else rest
        if len(out[-1]) + 1 + len(c) > width:
            out.append(c)
        else:
            out[-1] += " " + c
    out[-1] += "."
    return out


class DataWriter:
    """Writes items into a member and records data_items and copies facts. `resolve(member)`
    returns (path, items) of a copybook or (None, None) for one outside the estate."""

    def __init__(self, m: Member, resolve: Callable[[str], tuple[Optional[str], Optional[list[Item]]]]) -> None:
        self.m = m
        self.resolve = resolve

    def items(self, items: list[Item], section: Optional[str], depth: int = 0) -> None:
        for it in items:
            if "sql_include" in it:
                line = self.m.cobol(f"EXEC SQL INCLUDE {it['sql_include']} END-EXEC.")
                path, _ = self.resolve(it["sql_include"])
                self.m.fact("copies", member=it["sql_include"], kind="sql-include", line=line, resolves_to=path)
                continue
            if "copy_only" in it:
                with self.m.horror(it.get("horror")):
                    self._copy_lines([it["copy_only"]], it["copy_style"], None, depth)
                continue
            self.item(it, section, depth)

    def item(self, it: Item, section: Optional[str], depth: int) -> None:
        with self.m.horror(it.get("horror")):
            area = "A" if it["lvl"] in (1, 77) else "B"
            indent = 0 if area == "A" else 4 * max(depth - 1, 0)
            text = item_text(it) + "."
            if it["copy"] and it["copy_style"] == "same-line":
                text += "".join(f" COPY {c}." for c in it["copy"])
                text = text.replace(". COPY", ".  COPY", 1)
            room = 72 - 7 - (0 if area == "A" else 4 + indent)
            if len(text) <= room:
                line = self.m.cobol(text, area=area, indent=indent)
            else:
                # wrap the trailing clauses onto continuation lines, aligned under the PIC
                line = 0
                cont = indent + 23 - (4 if area == "A" else 0)
                if it["copy"] and it["copy_style"] == "same-line":
                    raise ValueError(f"{self.m.path}: a same-line COPY entry must fit one line")
                for chunk in _wrap(it, room, 72 - 7 - 4 - cont):
                    if line == 0:
                        line = self.m.cobol(chunk, area=area, indent=indent)
                    else:
                        self.m.cobol(chunk, indent=cont)
            self.m.fact(
                "data_items",
                level=it["lvl"],
                name=it["name"],
                pic=it.get("pic"),
                usage=norm_usage(it.get("usage")),
                occurs=it.get("occurs"),
                redefines=it.get("redefines"),
                value=it.get("value"),
                section=section,
                line=line,
                **({"copy_members": list(it["copy"])} if it["copy"] else {}),
            )
            if it["copy"]:
                if it["copy_style"] == "same-line":
                    for c in it["copy"]:
                        path, _ = self.resolve(c)
                        self.m.fact("copies", member=c, kind="copy", line=line, resolves_to=path)
                else:
                    self._copy_lines(it["copy"], it["copy_style"], None, depth + 1)
            self.items(it["kids"], section, depth + 1)

    def _copy_lines(self, members: list[str], style: str, _owner: Optional[str], depth: int) -> None:
        indent = 4 * max(depth - 1, 0)
        for c in members:
            path, _ = self.resolve(c)
            if style == "split":
                line = self.m.cobol("COPY", indent=indent)
                seq = self.m.seq_of(self.m.line_no)
                self.m.cobol(f"    {c}.", indent=indent)
                self.m.fact("copies", member=c, kind="copy", line=line, resolves_to=path)
                if seq:
                    self.m.phantom("copies", member=seq, why=f"the sequence number of the line after a split COPY, not the member ({c})")
            else:
                line = self.m.cobol(f"COPY {c}.", indent=indent)
                self.m.fact("copies", member=c, kind="copy", line=line, resolves_to=path)


def layout(root: Item, owner_path: str, resolve: Callable[[str], tuple[Optional[str], Optional[list[Item]]]],
           line: int) -> dict[str, Any]:
    """The storage layout of one 01 record, COPY expanded: every elementary item in storage
    order with its offset and length. An item inside an OCCURS group is listed once, at its
    first occurrence; its `bytes` carry only its own OCCURS. An item under a REDEFINES is
    listed with `overlay: true` at the offset it overlays."""
    fields: list[dict[str, Any]] = []
    unresolved: list[str] = []

    def kids_of(it: Item, path: str) -> list[tuple[Item, str]]:
        out = [(k, path) for k in it["kids"] if k["lvl"] != 88]
        for c in it["copy"]:
            cpath, citems = resolve(c)
            if cpath is None or citems is None:
                unresolved.append(c)
                continue
            out += [(k, cpath) for k in citems if "lvl" in k and k["lvl"] != 88]
        return out

    def size_of(it: Item, path: str) -> int:
        if it["lvl"] == 88:
            return 0
        kids = kids_of(it, path)
        if kids:
            own = sum(size_of(k, p) for k, p in kids if not k.get("redefines") and k["lvl"] != 88)
        else:
            own = elementary_bytes(it["pic"], it.get("usage")) if it.get("pic") else 0
        return own * (it.get("occurs") or 1)

    def walk(it: Item, path: str, offset: int, overlay: bool) -> None:
        kids = kids_of(it, path)
        if not kids:
            if it.get("pic"):
                fields.append({
                    "name": it["name"], "level": it["lvl"], "pic": it["pic"], "usage": norm_usage(it.get("usage")),
                    "offset": offset,
                    "bytes": elementary_bytes(it["pic"], it.get("usage")) * (it.get("occurs") or 1),
                    "file": path,
                    **({"overlay": True} if overlay else {}),
                })
            return
        at = offset
        starts: dict[str, int] = {}
        for k, p in kids:
            if k["lvl"] == 88:
                continue
            if k.get("redefines"):
                walk(k, p, starts[k["redefines"]], True)
                continue
            starts[k["name"]] = at
            walk(k, p, at, overlay)
            at += size_of(k, p)

    walk(root, owner_path, 0, False)
    return {"record": root["name"], "line": line, "bytes": None if unresolved else size_of(root, owner_path),
            "fields": fields, **({"unresolved": unresolved} if unresolved else {})}
