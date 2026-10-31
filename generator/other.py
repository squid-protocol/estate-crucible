"""JCL, PROCLIB, BMS, CSD and DCLGEN members."""

from __future__ import annotations

import re
from typing import Any, Iterator, Optional

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


UTILITIES = {"IDCAMS", "SORT", "ICETOOL", "IKJEFT01", "IKJEFT1B", "IEBGENER", "ICEGENER", "IEBCOPY"}


def _flatten(steps: list[dict[str, Any]], ctx: Optional[dict[str, Any]] = None) -> Iterator[tuple[dict[str, Any], Any]]:
    """The job's statements in order: ("if" / "else" / "endif", the IF block) markers around the
    steps they hold, and ("step", step) for each EXEC."""
    for st in steps:
        if "if" in st:
            yield "if", st
            for sub in _flatten(st["then"]):
                yield sub
            if st.get("else"):
                yield "else", st
                for sub in _flatten(st["else"]):
                    yield sub
            yield "endif", st
        else:
            yield "step", st


def _operands_of(lines: list[str]) -> str:
    """A control statement's operands: its lines joined, continuation marks dropped, verb removed."""
    text = " ".join(ln.strip().rstrip("-").strip() for ln in lines)
    return text.split(None, 1)[1] if len(text.split(None, 1)) > 1 else ""


def _write_jcl(m: Member, spec: dict[str, Any], program_paths: dict[str, str], proc: bool) -> None:
    owner = spec["name"]
    jp: dict[str, Any] = {"job": None, "proc": owner} if proc else {"job": owner, "proc": None}
    if proc:
        _jcl_stmt(m, owner, "PROC", spec.get("symbolics", []) or [""])
    else:
        _jcl_stmt(m, owner, "JOB", [spec.get("accounting", "(ACCT)"), f"'{spec['title'][:20]}'", "CLASS=A",
                                     "MSGCLASS=X", *spec.get("job_extra", []),
                                     *(["NOTIFY=&SYSUID"] if spec.get("notify", True) else [])])
        if spec.get("jcllib"):
            _jcl_stmt(m, "", "JCLLIB", [f"ORDER=({','.join(spec['jcllib'])})"])
    for c in spec.get("comments", []):
        m.raw(f"//* {c}".rstrip())
    ordinal = 0
    blocks: list[dict[str, Any]] = []  # the IF blocks open at this point, innermost last
    branch = "then"
    job_level = [("step", {"name": None, "dds_only": True, "dds": spec["job_dds"]})] if spec.get("job_dds") else []
    for kind, st in [*job_level, *_flatten(spec["steps"])]:
        if kind == "if":
            m.raw("//*")
            with m.horror(st.get("horror")):
                _jcl_stmt(m, st.get("name", ""), "IF", [f"({st['if']}) THEN"])
            blocks.append(st)
            branch = "then"
            continue
        if kind == "else":
            with m.horror(st.get("horror")):
                _jcl_stmt(m, "", "ELSE", [])
            branch = "else"
            continue
        if kind == "endif":
            with m.horror(st.get("horror")):
                _jcl_stmt(m, "", "ENDIF", [])
            blocks.pop()
            continue
        step = st
        if not step.get("dds_only"):
            ordinal += 1
            m.raw("//*")
            operands = [f"PGM={step['pgm']}"] if step.get("pgm") else [step["proc"], *step.get("proc_parms", [])]
            if step.get("cond"):
                operands.append(f"COND={step['cond']}")
            if step.get("parm"):
                operands.append(f"PARM='{step['parm']}'")
            if step.get("rd"):
                operands.append(f"RD={step['rd']}")
            for pstep, value in step.get("parm_overrides", []):
                operands.append(f"PARM.{pstep}='{value}'")
            for pstep, value in step.get("cond_overrides", []):
                operands.append(f"COND.{pstep}={value}")
            with m.horror(blocks[-1].get("horror") if blocks else None), m.horror(step.get("horror")):
                line = _jcl_stmt(m, step["name"], "EXEC", operands)
                extra: dict[str, Any] = {}
                if step.get("parm"):
                    extra["parm"] = step["parm"]
                if blocks:
                    extra["if_cond"] = blocks[-1]["if"]
                    extra["branch"] = branch
                if spec.get("restart") and not proc:
                    extra["restart"] = spec["restart"]
                    if spec.get("restart_checkid"):
                        extra["restart_checkid"] = spec["restart_checkid"]
                if step.get("rd"):
                    extra["rd"] = step["rd"]
                if step.get("parm_overrides"):
                    extra["parm_overrides"] = [{"step": a, "parm": b} for a, b in step["parm_overrides"]]
                if step.get("cond_overrides"):
                    extra["cond_overrides"] = [{"step": a, "cond": b} for a, b in step["cond_overrides"]]
                m.fact("jcl_steps", **jp, step=step["name"],
                       ordinal=ordinal, program=step.get("pgm"), exec_proc=step.get("proc"), cond=step.get("cond"),
                       line=line, **extra)
                if step.get("pgm"):
                    m.fact("call_sites", verb="EXEC PGM", form="literal", operand=step["pgm"], target=step["pgm"],
                           line=line, resolves_to=program_paths.get(step["pgm"]))
        prev_dd: Optional[str] = None
        for dd in step.get("dds", []):
            concat = dd.get("concat", False)
            if dd.get("sysout"):
                ops = [f"SYSOUT={dd['sysout']}", *dd.get("extra", [])]
            elif dd.get("inline") is not None:
                ops = ["*"]
            elif dd.get("dummy"):
                ops = ["DUMMY"]
            else:
                dsn = dd["dsn"] + (f"({dd['gen']})" if dd.get("gen") else "")
                ops = [f"DSN={dsn}", f"DISP={_disp(dd['disp'])}"] + dd.get("extra", [])
            temp = (dd.get("dsn") or "").startswith("&&")
            with m.horror(blocks[-1].get("horror") if blocks else None), m.horror(step.get("horror")), \
                    m.horror(dd.get("horror")):
                label = f"{dd['proc_step']}.{dd['name']}" if dd.get("proc_step") else dd["name"]
                dline = _jcl_stmt(m, "" if concat else label, "DD", ops)
                cards: list[tuple[int, str, str]] = []
                if dd.get("inline") is not None:
                    for card in dd["inline"]:
                        verb, lines = card if isinstance(card, tuple) else (None, card)
                        lines = [lines] if isinstance(lines, str) else lines
                        for i, ln in enumerate(lines):
                            at = m.raw(ln)
                            if verb and i == 0:
                                cards.append((at, verb, _operands_of(lines)))
                    m.raw("/*")
            if dd.get("dsn") and not temp:
                with m.horror(dd.get("horror")):
                    row = m.fact("jcl_datasets", dsn=dd["dsn"], generation=dd.get("gen"), step=step["name"],
                                 dd=prev_dd if concat else dd["name"], line=dline)
                    if (dd.get("gen") or "")[:1] in "+-" and dd.get("gen") and not row.get("horror"):
                        row["depends_on"] = ["H-0011"]  # #4331: a signed relative generation
            elif temp:
                with m.horror(dd.get("horror")):
                    m.phantom("jcl_datasets", "a temporary data set (&&name) exists only for the job: it is "
                              "not a dataset of the estate", dsn=dd["dsn"], step=step["name"], line=dline)
            disp: tuple[str, ...] = dd.get("disp") or ()
            extra = {}
            if temp:
                extra["temp"] = True
            if concat:
                extra["concat_of"] = prev_dd
            if dd.get("dummy"):
                extra["dummy"] = True
            if dd.get("proc_step"):
                extra["override_of"] = dd["proc_step"]
            symbolic = (dd.get("dsn") or "").startswith("&") and not temp
            if symbolic:
                extra["symbolic"] = True
            if dd.get("inline") is not None:
                extra["inline_lines"] = len(dd["inline"]) and sum(
                    1 if isinstance(c, str) else (1 if isinstance(c[1], str) else len(c[1])) for c in dd["inline"])
            # a DD that is a plain dataset reference tags only its jcl_datasets row (H-0011 and the
            # older horrors); a DD of a new form (temp, concatenated, inline, dummy) tags its jcl_dds fact
            new_form = temp or symbolic or concat or step.get("dds_only") or dd.get("proc_step") or dd.get("dummy") or dd.get("inline") is not None
            with m.horror((blocks[-1].get("horror") if blocks else None) if new_form else None), \
                    m.horror(step.get("horror") if new_form else None), m.horror(dd.get("horror") if new_form else None):
                m.fact("jcl_dds", **jp, step=step["name"],
                       dd=None if concat else dd["name"], dsn=dd.get("dsn"), generation=dd.get("gen"),
                       disp=disp[0] if disp else None, disp_normal=disp[1] if len(disp) > 1 else None,
                       sysout=dd.get("sysout"), line=dline, **extra)
                for at, verb, operands in cards:
                    m.fact("jcl_utility_cards", **jp, step=step["name"], utility=step.get("pgm"), dd=dd["name"],
                           verb=verb, operands=operands, line=at)
                    run = re.search(r"PROGRAM\((\w+)\)", operands) if verb == "RUN" else None
                    if run and step.get("pgm") == "IKJEFT01":
                        m.fact("call_sites", verb="RUN PROGRAM", form="literal", operand=run.group(1),
                               target=run.group(1), line=at, resolves_to=program_paths.get(run.group(1)))
            if not concat:
                prev_dd = dd["name"]
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
        # `_horror` in attrs tags the definition's facts
        horror = attrs.get("_horror")
        attrs = {k: v for k, v in attrs.items() if not k.startswith("_")}
        text = f"DEFINE {rtype}({name}) GROUP({group})" + "".join(f" {k}({v})" for k, v in attrs.items())
        with m.horror(horror):
            line = m.raw(text)
            m.fact("csd_resources", type=rtype, name=name, group=group, line=line,
                   **{k.lower(): v for k, v in attrs.items() if k in ("PROGRAM", "DSNAME")})
            if rtype == "TRANSACTION":
                m.fact("transactions", transid=name, program=attrs["PROGRAM"], group=group, line=line,
                       resolves_to=program_paths.get(attrs["PROGRAM"]))
    m.compile = {"status": "not-cobol"}


# ------------------------------------------------------------------ CICS macro tables (HLASM)


def _asm_card(text: str, cont: str = " ", seq: Optional[int] = None) -> str:
    """One 80-column assembler card: cols 1-71 statement field, col 72 continuation indicator,
    cols 73-80 sequence field (or trimmed when unnumbered and uncontinued)."""
    if len(text) > 71:
        raise ValueError(f"assembler statement field past column 71: {text!r}")
    if seq is not None:
        return text.ljust(71) + cont + f"{seq:08d}"
    return text.ljust(71) + cont if cont != " " else text.rstrip()


def _wrap_macro_operands(head_prefix: str, operands: list[str], remark: str = "") -> list[tuple[str, str]]:
    """Wrap macro operands into <= 71-column assembler lines (col 16 continuation)."""
    lines: list[tuple[str, str]] = []
    cur: list[str] = []
    for opnd in operands:
        prefix_len = len(head_prefix) if not lines else 15
        candidate = ",".join(cur + [opnd])
        # Leave 1 char for trailing comma if another line follows
        if cur and prefix_len + len(candidate) + 1 > 71:
            lines.append((",".join(cur) + ",", ""))
            cur = [opnd]
        else:
            cur.append(opnd)
    lines.append((",".join(cur), remark))
    return lines


def write_macro_table(m: Member, spec: dict[str, Any], program_paths: dict[str, str]) -> None:
    """An HLASM member holding CICS resource-definition macro tables (DFHFCT, DFHPCT, DFHPPT,
    DFHDCT, DFHTST, DFHSRT, DFHJCT, DFHTCT, DFHMCT, DFHSIT)."""
    with m.horror(spec.get("horror")):
        _write_macro_table(m, spec, program_paths)
    m.compile = {"status": "not-cobol"}


def _write_macro_table(m: Member, spec: dict[str, Any], program_paths: dict[str, str]) -> None:
    numbered = spec.get("numbered", False)

    def emit(text: str, cont: str = " ") -> int:
        seq = m.line_no * 100 if numbered else None
        return m.raw(_asm_card(text, cont, seq))

    for c in spec.get("comments", []):
        emit(f"* {c}")
    if spec.get("csect"):
        emit(f"{spec['csect']:<8} CSECT")
    suffix: dict[str, str] = {}
    sdsci: dict[str, dict[str, str]] = {}
    for st in spec["statements"]:
        if st.get("comment"):
            emit(f"* {st['comment']}")
            continue
        op = st["op"].upper()
        label = st.get("label", "")
        head_prefix = f"{label:<8} {op:<6} " if len(label) <= 8 else f"{label} {op} "
        lines_spec: list[tuple[str, str]] = st.get("lines") or _wrap_macro_operands(
            head_prefix, st["operands"], st.get("remark", "")
        )
        first = m.line_no
        for idx, (ops_part, remark) in enumerate(lines_spec):
            prefix = head_prefix if idx == 0 else " " * 15
            body = prefix + ops_part + (f"  {remark}" if remark else "")
            cont = "X" if idx < len(lines_spec) - 1 else " "
            emit(body, cont)
        # Key what the macro statement defines per IBM documentation:
        with m.horror(st.get("horror")):
            for ph in st.get("phantoms", []):
                m.phantom(**ph)
            kv = dict(st.get("kv") or {})
            for ops_part, _remark in lines_spec:
                if ops_part.startswith(" "):
                    # HLASM rule (SC26-4940-05 p.15, p.296): a continuation line starting after col 16 is a remark
                    break
                for piece in ops_part.split(","):
                    if "=" in piece and "(" not in piece and ")" not in piece:
                        k, v = piece.split("=", 1)
                        kv.setdefault(k.strip().upper(), v.strip().strip("'\""))
            kind = kv.get("TYPE", "").upper()
            if kind == "INITIAL" and kv.get("SUFFIX"):
                suffix.setdefault(op, kv["SUFFIX"].upper())
            if op == "DFHDCT" and kind == "SDSCI" and kv.get("DSCNAME"):
                sdsci[kv["DSCNAME"].upper()] = kv
            for fact in st.get("facts", []):
                ch = fact["channel"]
                vals = {k: v for k, v in fact.items() if k != "channel"}
                vals["line"] = first
                if ch == "transactions" and "resolves_to" not in vals:
                    vals["resolves_to"] = program_paths.get(vals["program"])
                m.fact(ch, **vals)
    emit("         END")


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

