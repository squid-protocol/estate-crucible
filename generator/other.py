"""JCL, PROCLIB, BMS, CSD and DCLGEN members."""

from __future__ import annotations

from typing import Any

from .data import DataWriter, I, Item
from .model import Member

# ------------------------------------------------------------------ JCL


def _jcl_stmt(m: Member, name: str, op: str, operands: list[str]) -> int:
    """Write `//name op operands`, continuing on `//` lines (operand field from col 16) when
    a line would pass col 71. Returns the first line's number."""
    first = m.line_no
    head = f"//{name:<8} {op} "
    line = head
    for i, opnd in enumerate(operands):
        piece = opnd + ("," if i < len(operands) - 1 else "")
        if len(line) + len(piece) > 71 and line != head:
            m.raw(line)
            line = "//" + " " * 13 + piece
        else:
            line += piece
    m.raw(line.rstrip())
    return first


def _disp(d: tuple[str, ...]) -> str:
    return d[0] if len(d) == 1 else "(" + ",".join(d) + ")"


def write_jcl(m: Member, spec: dict[str, Any], program_paths: dict[str, str], *, proc: bool) -> None:
    """A job (proc=False) or a cataloged procedure (proc=True)."""
    with m.horror(spec.get("horror")):
        _write_jcl(m, spec, program_paths, proc)


def _write_jcl(m: Member, spec: dict[str, Any], program_paths: dict[str, str], proc: bool) -> None:
    owner = spec["name"]
    if proc:
        _jcl_stmt(m, owner, "PROC", spec.get("symbolics", []) or [""])
    else:
        _jcl_stmt(m, owner, "JOB", [spec.get("accounting", "(ACCT)"), f"'{spec['title'][:20]}'", "CLASS=A",
                                     "MSGCLASS=X", "NOTIFY=&SYSUID"])
    for c in spec.get("comments", []):
        m.raw(f"//* {c}".rstrip())
    for ordinal, step in enumerate(spec["steps"], start=1):
        m.raw("//*")
        operands = [f"PGM={step['pgm']}"] if step.get("pgm") else [step["proc"]]
        if step.get("cond"):
            operands.append(f"COND={step['cond']}")
        if step.get("parm"):
            operands.append(f"PARM='{step['parm']}'")
        line = _jcl_stmt(m, step["name"], "EXEC", operands)
        m.fact("jcl_steps", job=None if proc else owner, proc=owner if proc else None, step=step["name"],
               ordinal=ordinal, program=step.get("pgm"), exec_proc=step.get("proc"), cond=step.get("cond"), line=line)
        if step.get("pgm"):
            m.fact("call_sites", verb="EXEC PGM", form="literal", operand=step["pgm"], target=step["pgm"], line=line,
                   resolves_to=program_paths.get(step["pgm"]))
        for dd in step.get("dds", []):
            if dd.get("sysout"):
                ops = [f"SYSOUT={dd['sysout']}"]
            else:
                dsn = dd["dsn"] + (f"({dd['gen']})" if dd.get("gen") else "")
                ops = [f"DSN={dsn}", f"DISP={_disp(dd['disp'])}"] + dd.get("extra", [])
            with m.horror(dd.get("horror")):
                dline = _jcl_stmt(m, dd["name"], "DD", ops)
            if dd.get("dsn"):
                with m.horror(dd.get("horror")):
                    row = m.fact("jcl_datasets", dsn=dd["dsn"], generation=dd.get("gen"), step=step["name"],
                                 dd=dd["name"], line=dline)
                    if (dd.get("gen") or "")[:1] in "+-" and dd.get("gen") and not row.get("horror"):
                        row["depends_on"] = ["H-0011"]  # #4331: a signed relative generation
            disp: tuple[str, ...] = dd.get("disp") or ()
            m.fact("jcl_dds", job=None if proc else owner, proc=owner if proc else None, step=step["name"],
                   dd=dd["name"], dsn=dd.get("dsn"), generation=dd.get("gen"),
                   disp=disp[0] if disp else None, disp_normal=disp[1] if len(disp) > 1 else None,
                   sysout=dd.get("sysout"), line=dline)
    if proc:
        m.raw("//         PEND")
    m.compile = {"status": "not-cobol"}


# ------------------------------------------------------------------ BMS


def _bms_macro(m: Member, label: str, op: str, operands: list[str]) -> int:
    """label in cols 1-8, op from col 10, operands from col 16, continued with X in col 72."""
    first = m.line_no
    chunks: list[str] = []
    cur = ""
    for i, o in enumerate(operands):
        piece = o + ("," if i < len(operands) - 1 else "")
        if cur and len(cur) + len(piece) > 55:
            chunks.append(cur)
            cur = piece
        else:
            cur += piece
    chunks.append(cur)
    for i, ch in enumerate(chunks):
        text = (f"{label:<8} {op:<6} " if i == 0 else " " * 15) + ch
        m.raw(text.ljust(71) + "X" if i < len(chunks) - 1 else text.rstrip())
    return first


def write_bms(m: Member, spec: dict[str, Any]) -> None:
    with m.horror(spec.get("horror")):
        _write_bms(m, spec)
    m.compile = {"status": "not-cobol"}


def _write_bms(m: Member, spec: dict[str, Any]) -> None:
    ms = spec["mapset"]
    line = _bms_macro(m, ms, "DFHMSD", ["TYPE=&SYSPARM", "MODE=INOUT", "LANG=COBOL", "STORAGE=AUTO",
                                         "CTRL=(FREEKB,FRSET)", "TIOAPFX=YES"])
    m.fact("screen_fields", kind="mapset", mapset=ms, map=None, name=ms, line=line)
    for mp in spec["maps"]:
        line = _bms_macro(m, mp["name"], "DFHMDI", [f"SIZE=({mp['size'][0]},{mp['size'][1]})", "LINE=1", "COLUMN=1"])
        m.fact("screen_fields", kind="map", mapset=ms, map=mp["name"], name=mp["name"], line=line)
        for f in mp["fields"]:
            ops = [f"POS=({f['pos'][0]},{f['pos'][1]})", f"LENGTH={f['length']}", f"ATTRB=({f['attrb']})"]
            if f.get("picin"):
                ops.append(f"PICIN='{f['picin']}'")
            if f.get("initial") is not None:
                ops.append(f"INITIAL='{f['initial']}'")
            line = _bms_macro(m, f.get("name") or "", "DFHMDF", ops)
            m.fact("screen_fields", kind="field", mapset=ms, map=mp["name"], name=f.get("name"),
                   pos_line=f["pos"][0], pos_column=f["pos"][1], length=f["length"], attrb=f["attrb"],
                   picin=f.get("picin"), initial=f.get("initial"), line=line)
    _bms_macro(m, "", "DFHMSD", ["TYPE=FINAL"])
    m.raw("         END")
    m.compile = {"status": "not-cobol"}


def symbolic_map(spec: dict[str, Any]) -> list[Item]:
    """The symbolic description map BMS generates for a mapset (TIOAPFX=YES): per map an input
    record (L/F/A/I per named field) and an output record redefining it (O per field)."""
    items: list[Item] = []
    for mp in spec["maps"]:
        named = [f for f in mp["fields"] if f.get("name")]
        inp = [I(2, "FILLER", "X(12)")]
        out = [I(2, "FILLER", "X(12)")]
        for f in named:
            n = f["name"]
            inp += [I(2, n + "L", "S9(4)", "COMP"), I(2, n + "F", "X"),
                    I(2, "FILLER", redefines=n + "F", kids=[I(3, n + "A", "X")]),
                    I(2, n + "I", f"X({f['length']})")]
            out += [I(2, "FILLER", "X(3)"), I(2, n + "O", f"X({f['length']})")]
        items.append(I(1, mp["name"] + "I", kids=inp))
        items.append(I(1, mp["name"] + "O", redefines=mp["name"] + "I", kids=out))
    return items


# ------------------------------------------------------------------ CSD


def write_csd(m: Member, spec: dict[str, Any], program_paths: dict[str, str]) -> None:
    group = spec["group"]
    m.raw(f"* CSD GROUP {group} -- {spec['title']}")
    for rtype, name, attrs in spec["defines"]:
        text = f"DEFINE {rtype}({name}) GROUP({group})" + "".join(f" {k}({v})" for k, v in attrs.items())
        line = m.raw(text)
        m.fact("csd_resources", type=rtype, name=name, group=group, line=line,
               **{k.lower(): v for k, v in attrs.items() if k in ("PROGRAM", "DSNAME")})
        if rtype == "TRANSACTION":
            m.fact("transactions", transid=name, program=attrs["PROGRAM"], group=group, line=line,
                   resolves_to=program_paths.get(attrs["PROGRAM"]))
    m.compile = {"status": "not-cobol"}


# ------------------------------------------------------------------ DCLGEN


def write_dclgen(m: Member, spec: dict[str, Any]) -> None:
    """A DCLGEN member: the DECLARE TABLE and the COBOL host structure."""
    with m.horror(spec.get("horror")):
        _dclgen(m, spec)
    m.compile = {"status": "copybook"}


def _dclgen(m: Member, spec: dict[str, Any]) -> None:
    table = spec["table"]
    m.comment("*" * 63)
    m.comment(f" DCLGEN TABLE({table})".ljust(62) + "*")
    m.comment(f"        LIBRARY({spec['library']})".ljust(62) + "*")
    m.comment("        LANGUAGE(COBOL) QUOTE".ljust(62) + "*")
    m.comment("*" * 63)
    tline = m.cobol(f"EXEC SQL DECLARE {table} TABLE")
    cols = []
    for i, (name, typ, length, scale, nullable) in enumerate(spec["columns"]):
        tdesc = typ + (f"({length}, {scale})" if scale is not None else f"({length})" if length else "")
        text = ("( " if i == 0 else "  ") + f"{name:<30} {tdesc}" + ("" if nullable else " NOT NULL")
        text += "," if i < len(spec["columns"]) - 1 else ""
        cline = m.cobol(text)
        cols.append({"name": name, "type": typ, "length": length, "scale": scale, "nullable": nullable, "line": cline})
    m.cobol(") END-EXEC.")
    m.fact("sql_tables", table=table, line=tline, columns=cols)
    m.comment("*" * 63)
    m.comment(f" COBOL DECLARATION FOR TABLE {table}".ljust(62) + "*")
    m.comment("*" * 63)
    kids: list[Item] = []
    for name, typ, length, scale, _ in spec["columns"]:
        cname = name.replace("_", "-")
        if typ == "CHAR":
            kids.append(I(10, cname, f"X({length})"))
        elif typ == "VARCHAR":
            kids.append(I(10, cname, kids=[I(49, cname + "-LEN", "S9(4)", "USAGE COMP"),
                                           I(49, cname + "-TEXT", f"X({length})")]))
        elif typ == "DECIMAL":
            pic = f"S9({length - scale})V9({scale})" if scale else f"S9({length})"
            kids.append(I(10, cname, pic, "USAGE COMP-3"))
        elif typ == "INTEGER":
            kids.append(I(10, cname, "S9(9)", "USAGE COMP"))
        elif typ == "DATE":
            kids.append(I(10, cname, "X(10)"))
        else:
            raise ValueError(typ)
    DataWriter(m, lambda *_a: (None, None)).items([I(1, spec["structure"], kids=kids)], None)
    m.comment("*" * 63)
    m.comment(f" THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS {len(cols)}".ljust(62) + "*")
    m.comment("*" * 63)

