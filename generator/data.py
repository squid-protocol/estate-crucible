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


Copy = dict[str, Any]
Resolver = Callable[..., tuple[Optional[str], Optional[list[Item]]]]


def CP(member: str, *, lib: Optional[str] = None, quoted: bool = False,
       replacing: Optional[tuple[str, str]] = None, sep: str = " ") -> Copy:
    """One COPY statement: `COPY member [IN lib] [REPLACING ==a== BY ==b==]`, or `COPY 'member'`.
    `sep` is the separator after COPY (a full-width space U+3000 in some Japanese estates)."""
    return {"member": member, "lib": lib, "quoted": quoted, "replacing": replacing, "sep": sep}


def _cp(c: Any) -> Copy:
    return c if isinstance(c, dict) else CP(c)


def I(lvl: int, name: Optional[str], pic: Optional[str] = None, usage: Optional[str] = None, *,  # noqa: E741 -- the DSL's item constructor
      occurs: Optional[int] = None, redefines: Optional[str] = None, value: Optional[str] = None,
      sign: Optional[str] = None, kids: Optional[list[Item]] = None, copy: Optional[list[Any]] = None,
      copy_style: str = "next-line", horror: Optional[str] = None,
      depends_on: Optional[list[str]] = None, seq: Optional[str] = None, sep: Optional[str] = None) -> Item:
    """One data description entry. `name` None writes no data-name (an implicit FILLER).
    `sign` is a SIGN clause body (`LEADING SEPARATE`). `copy` makes it a group whose
    subordinate entries come from COPY statements (member names or CP(...)); `copy_style`
    is how they are written: next-line, same-line (`01 X. COPY Y.`, several on one line)
    or split (`COPY` / member on the next line)."""
    return {"lvl": lvl, "name": name, "pic": pic, "usage": usage, "occurs": occurs, "redefines": redefines,
            "value": value, "sign": sign, "kids": kids or [], "copy": [_cp(c) for c in copy or []],
            "copy_style": copy_style, "horror": horror, "depends_on": depends_on, "seq": seq, "sep": sep}


def C(member: Any, *, horror: Optional[str] = None, style: str = "next-line",
      depends_on: Optional[list[str]] = None) -> Item:
    """A bare COPY of a member that holds whole records (01 levels of its own)."""
    return {"copy_only": _cp(member), "copy_style": style, "horror": horror, "depends_on": depends_on}


def SQLINC(member: str, *, horror: Optional[str] = None) -> Item:
    """EXEC SQL INCLUDE member END-EXEC."""
    return {"sql_include": member, "horror": horror}


_PIC_REPEAT = re.compile(r"(.)\((\d+)\)")


def pic_positions(pic: str) -> str:
    """The PICTURE string with every `x(n)` repeat expanded."""
    return _PIC_REPEAT.sub(lambda m: m.group(1) * int(m.group(2)), pic.upper())


def elementary_bytes(pic: str, usage: Optional[str], sign: Optional[str] = None) -> int:
    """Bytes of one elementary item. SIGN ... SEPARATE gives the sign a byte of its own."""
    expanded = pic_positions(pic)
    if "N" in expanded or "G" in expanded:
        # national (USAGE NATIONAL) and DBCS (USAGE DISPLAY-1): 2 bytes per character position
        return 2 * sum(1 for ch in expanded if ch in "NG")
    if sign and "SEPARATE" in sign.upper():
        return sum(1 for ch in expanded if ch not in "SVP") + 1
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


def implied_usage(pic: Optional[str]) -> Optional[str]:
    """A PICTURE of N (NSYMBOL(NATIONAL), the default) implies USAGE NATIONAL, of G USAGE
    DISPLAY-1; an implied DISPLAY is recorded as no usage."""
    if not pic:
        return None
    p = pic_positions(pic)
    return "NATIONAL" if "N" in p else "DISPLAY-1" if "G" in p else None


def norm_usage(usage: Optional[str]) -> Optional[str]:
    """`USAGE COMP` and `COMP` are the same clause; the key records the usage word alone."""
    if not usage:
        return None
    u = usage.upper().strip()
    return u[len("USAGE "):].strip() if u.startswith("USAGE ") else u


def item_clauses(it: Item) -> list[str]:
    parts = []
    if it.get("sign"):
        parts.append(f"SIGN {it['sign']}")
    if it.get("redefines"):
        parts.append(f"REDEFINES {it['redefines']}")
    if it.get("pic"):
        parts.append(f"PIC {it['pic']}")
    if it.get("usage"):
        parts.append(it["usage"])
    if parts and parts[0].startswith("SIGN "):
        parts.append(parts.pop(0))
    if it.get("occurs"):
        parts.append(f"OCCURS {it['occurs']} TIMES")
    if it.get("value") is not None:
        parts.append(f"VALUE {it['value']}")
    return parts


def item_text(it: Item) -> str:
    if it.get("sep"):
        # every separator written as `sep` (a full-width space, #3956)
        return it["sep"].join([f"{it['lvl']:02d}", *([it["name"]] if it.get("name") else []),
                               *(c.replace(" ", it["sep"]) for c in item_clauses(it))])
    head = f"{it['lvl']:02d}  {it['name']}" if it.get("name") else f"{it['lvl']:02d}"
    rest = " ".join(item_clauses(it))
    if not rest:
        return head
    # line the PIC up in a column, the way most shops keep a record layout
    return f"{head:<27}{rest}" if len(head) < 27 else f"{head} {rest}"


def _wrap(it: Item, first: int, rest: int) -> list[str]:
    """Split an entry at clause boundaries to fit the line widths: the head and as many
    clauses as fit, then the rest on continuation lines."""
    clauses = item_clauses(it)
    out = [item_text({**it, "redefines": None, "pic": None, "usage": None, "occurs": None, "value": None,
                      "sign": None})]
    for c in clauses:
        width = first if len(out) == 1 else rest
        if len(out[-1]) + 1 + len(c) > width:
            out.append(c)
        else:
            out[-1] += " " + c
    out[-1] += "."
    return out


def copy_text(c: Copy) -> str:
    name = f"'{c['member']}'" if c["quoted"] else c["member"]
    lib = f" IN {c['lib']}" if c["lib"] else ""
    rep = f" REPLACING =={c['replacing'][0]}== BY =={c['replacing'][1]}==" if c["replacing"] else ""
    return f"COPY{c.get('sep', ' ')}{name}{lib}{rep}."


def is_data_name(name: Optional[str]) -> bool:
    """Pseudo-text awaiting COPY REPLACING (`:TAG:-ID`) is not a COBOL word: `:` is not a
    character of a user-defined word."""
    return name is None or ":" not in name


def replaced(items: list[Item], rep: Optional[tuple[str, str]]) -> list[Item]:
    """Copybook items as a COPY ... REPLACING ==a== BY ==b== sees them (partial-word: `a`
    is replaced inside each name)."""
    if not rep:
        return items

    def sub(it: Item) -> Item:
        out = dict(it)
        for k in ("name", "redefines"):
            if out.get(k):
                out[k] = out[k].replace(rep[0], rep[1])
        out["kids"] = [sub(k) for k in it.get("kids", [])]
        return out

    return [sub(it) for it in items]


class DataWriter:
    """Writes items into a member and records data_items and copies facts. `resolve(member,
    lib)` returns (path, items) of a copybook or (None, None) for one outside the estate."""

    def __init__(self, m: Member, resolve: Resolver) -> None:
        self.m = m
        self.resolve = resolve

    def items(self, items: list[Item], section: Optional[str], depth: int = 0) -> None:
        for it in items:
            if "sql_include" in it:
                line = self.m.cobol(f"EXEC SQL INCLUDE {it['sql_include']} END-EXEC.")
                path, _ = self.resolve(it["sql_include"], None)
                with self.m.horror(it.get("horror")):
                    self.m.fact("copies", member=it["sql_include"], kind="sql-include", line=line, resolves_to=path)
                continue
            if "copy_only" in it:
                with self.m.horror(it.get("horror")):
                    self._copy_lines([it["copy_only"]], it["copy_style"], depth, it.get("depends_on"))
                continue
            self.item(it, section, depth)

    def item(self, it: Item, section: Optional[str], depth: int) -> None:
        with self.m.horror(it.get("horror")):
            area = "A" if it["lvl"] in (1, 77) else "B"
            indent = 0 if area == "A" else 4 * max(depth - 1, 0)
            if self.m.free:
                # free format: entries indented by level (`    01 VALUE-BYTES.`, #4203)
                area, indent = "B", 3 * depth
            text = item_text(it) + "."
            if it["copy"] and it["copy_style"] == "same-line":
                text += "".join(" " + copy_text(c) for c in it["copy"])
                text = text.replace(". COPY", ".  COPY", 1)
            room = 72 - 7 - (0 if area == "A" else 4 + indent)
            if len(text) <= room:
                # `seq`: a change marker in cols 1-6 instead of the sequence number (#3348)
                line = self.m.cobol(text, area=area, indent=indent, seq=it.get("seq"))
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
            if is_data_name(it["name"]):
                sign = (it.get("sign") or "").upper()
                self.m.fact(
                    "data_items",
                    level=it["lvl"],
                    name=it["name"] or "FILLER",
                    pic=it.get("pic"),
                    usage=norm_usage(it.get("usage")) or implied_usage(it.get("pic")),
                    occurs=it.get("occurs"),
                    redefines=it.get("redefines"),
                    value=it.get("value"),
                    section=section,
                    line=line,
                    **({"implicit_filler": True} if not it["name"] else {}),
                    **({"sign_separate": "SEPARATE" in sign, "sign_leading": "LEADING" in sign} if sign else {}),
                    **({"copy_members": [c["member"] for c in it["copy"]]} if it["copy"] else {}),
                    **({"depends_on": it["depends_on"]} if it.get("depends_on") else {}),
                )
            else:
                self.m.phantom("data_items", name=it["name"], line=line,
                               why=f"{it['name']} is pseudo-text awaiting COPY REPLACING, not a data-name")
            if it["copy"]:
                if it["copy_style"] == "same-line":
                    for c in it["copy"]:
                        path, _ = self.resolve(c["member"], c["lib"])
                        self.m.fact("copies", member=c["member"], kind="copy", line=line, resolves_to=path)
                else:
                    self._copy_lines(it["copy"], it["copy_style"], depth + 1, None)
            self.items(it["kids"], section, depth + 1)

    def _copy_lines(self, copies: list[Copy], style: str, depth: int, depends_on: Optional[list[str]]) -> None:
        indent = 4 * max(depth - 1, 0)
        for c in copies:
            path, _ = self.resolve(c["member"], c["lib"])
            extra: dict[str, Any] = {}
            if c["lib"]:
                extra["library"] = c["lib"]
            if c["replacing"]:
                extra["replacing"] = list(c["replacing"])
            if depends_on:
                extra["depends_on"] = depends_on
            if style == "split":
                line = self.m.cobol("COPY", indent=indent)
                seq = self.m.seq_of(self.m.line_no)
                self.m.cobol(f"    {copy_text(c)[5:]}", indent=indent)
                self.m.fact("copies", member=c["member"], kind="copy", line=line, resolves_to=path, **extra)
                if seq:
                    self.m.phantom("copies", member=seq,
                                   why=f"the sequence number of the line after a split COPY, not the member ({c['member']})")
            else:
                line = self.m.cobol(copy_text(c), indent=indent)
                self.m.fact("copies", member=c["member"], kind="copy", line=line, resolves_to=path, **extra)


def layout(root: Item, owner_path: str, resolve: Resolver, line: int) -> dict[str, Any]:
    """The storage layout of one 01 record, COPY expanded (REPLACING applied): every
    elementary item in storage order with its offset and length. An item inside an OCCURS
    group is listed once, at its first occurrence; its `bytes` carry only its own OCCURS. An
    item under a REDEFINES is listed with `overlay: true` at the offset it overlays."""
    fields: list[dict[str, Any]] = []
    unresolved: list[str] = []

    def kids_of(it: Item, path: str) -> list[tuple[Item, str]]:
        out = [(k, path) for k in it["kids"] if k["lvl"] != 88]
        for c in it["copy"]:
            cpath, citems = resolve(c["member"], c["lib"])
            if cpath is None or citems is None:
                unresolved.append(c["member"])
                continue
            out += [(k, cpath) for k in replaced(citems, c["replacing"]) if "lvl" in k and k["lvl"] != 88]
        return out

    def size_of(it: Item, path: str) -> int:
        if it["lvl"] == 88:
            return 0
        kids = kids_of(it, path)
        if kids:
            own = sum(size_of(k, p) for k, p in kids if not k.get("redefines") and k["lvl"] != 88)
        else:
            own = elementary_bytes(it["pic"], it.get("usage"), it.get("sign")) if it.get("pic") else 0
        return own * (it.get("occurs") or 1)

    def walk(it: Item, path: str, offset: int, overlay: bool) -> None:
        kids = kids_of(it, path)
        if not kids:
            if it.get("pic"):
                fields.append({
                    "name": it["name"] or "FILLER", "level": it["lvl"], "pic": it["pic"],
                    "usage": norm_usage(it.get("usage")) or implied_usage(it["pic"]),
                    "offset": offset,
                    "bytes": elementary_bytes(it["pic"], it.get("usage"), it.get("sign")) * (it.get("occurs") or 1),
                    "file": path,
                    **({"overlay": True} if overlay else {}),
                })
            return
        at = offset
        starts: dict[str, int] = {}
        for k, p in kids:
            if k.get("redefines"):
                walk(k, p, starts[k["redefines"]], True)
                continue
            if k["name"]:
                starts[k["name"]] = at
            walk(k, p, at, overlay)
            at += size_of(k, p)

    walk(root, owner_path, 0, False)
    return {"record": root["name"], "line": line, "bytes": None if unresolved else size_of(root, owner_path),
            "fields": fields, **({"unresolved": unresolved} if unresolved else {})}
