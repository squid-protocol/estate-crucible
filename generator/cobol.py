"""Renders a COBOL program or copybook spec into a Member, recording its facts."""

from __future__ import annotations

from typing import Any, Optional

from .data import DataWriter, Item, Resolver, layout
from .model import Member
from .moves import cobol_moves
from .stmt import Stmt

# How the compile check treats a member (SPEC.md, "Validity"). The status is part of the key.
COMPILED = "compiled"  # cobc -std=ibm, as written
STUBBED = "compiled-stubbed"  # cobc -std=ibm after EXEC SQL / EXEC CICS are replaced by CONTINUE
IBM_ONLY = "ibm-only"  # not compiled; `reason` says why


class ProgramWriter:
    """Writes one program (and the programs nested in it) into a member."""

    def __init__(self, m: Member, spec: dict[str, Any], resolve: Resolver, program_paths: dict[str, str],
                 multi: bool) -> None:
        self.m = m
        self.spec = spec
        self.resolve = resolve
        self.program_paths = program_paths
        self.multi = multi  # the member holds more than one program: units carry `program`
        self.unit: Optional[str] = None
        self.tag: Optional[str] = None
        self.exit_performs: list[tuple[int, Optional[str], Optional[str]]] = []
        self.idents: dict[str, str] = {}

    # ------------------------------------------------------------ helpers
    def line(self, text: str, indent: int = 0, area: str = "B", seq: Optional[str] = None) -> int:
        return self.m.cobol(text, area=area, indent=indent, tag=self.tag, seq=seq)

    def prog(self) -> dict[str, Any]:
        return {"program": self.spec["program_id"]} if self.multi else {}

    def edge(self, kind: str, target: str, line: int, **extra: Any) -> None:
        self.m.fact("edges", kind=kind, **{"from": self.unit}, target=target, line=line, **extra, **self.prog())

    # ------------------------------------------------------------ divisions
    def write(self) -> None:
        s = self.spec
        m = self.m
        with m.horror(s.get("banner_horror")):
            # a legacy banner ahead of the IDENTIFICATION DIVISION header: `*` comment lines,
            # `/` page ejects, and whatever prose the maintainers wrote in them
            for text in s.get("banner", []):
                indicator, text = (text[0], text[1:]) if text[:1] in "*/" else ("*", text)
                m.cobol(text, area="A", indicator=indicator)
        m.cobol("IDENTIFICATION DIVISION.", area="A")
        self.program_id()
        for label in ("AUTHOR", "INSTALLATION", "DATE-WRITTEN"):
            value = s.get(label.lower().replace("-", "_"))
            if value:
                m.cobol(f"{label + '.':<14}{value}.", area="A")
        if s.get("remarks"):
            m.comment("-" * 60)
            for r in s["remarks"]:
                m.comment(f" {r}")
            m.comment("-" * 60)
        self.environment()
        self.data()
        self.procedure()
        self.resolve_exit_performs()
        for ph in s.get("phantoms", []):
            with m.horror(ph.get("horror")):
                m.phantom(**{k: v for k, v in ph.items() if k != "horror"})
        for nested in s.get("nested", []):
            ProgramWriter(m, nested, self.resolve, self.program_paths, True).write()
        if self.multi:
            pid = s["program_id"]
            m.cobol(f"END PROGRAM {repr_name(pid, s)}.", area="A")

    def program_id(self) -> None:
        s = self.spec
        style = s.get("program_id_style", "normal")
        name = s["program_id"]
        with self.m.horror(s.get("program_id_horror")):
            if style == "normal":
                line = self.m.cobol(f"PROGRAM-ID.    {name}.", area="A")
            elif style == "padded-no-period":
                # the name and then blanks to column 72, no separator period (#4307 shape 1)
                line = self.m.cobol(f"PROGRAM-ID.    {name}", area="A", pad=True)
            elif style == "keyword-no-period":
                # no period after the PROGRAM-ID keyword (#4307 shape 2)
                line = self.m.cobol(f"PROGRAM-ID {name}.", area="A")
            elif style == "quoted":
                # the program-name as an alphanumeric literal (#4242)
                line = self.m.cobol(f"PROGRAM-ID. '{name}'.", indent=-3)
            elif style == "next-line":
                # PROGRAM-ID. alone, the name on the next line (#3418)
                line = self.m.cobol("PROGRAM-ID.", area="A")
                self.m.cobol(f"{name}.")
                if self.m.numbered:
                    self.m.phantom("programs", program_id=self.m.seq_of(line + 1),
                                   why="the next line's sequence number, not the program-name")
            else:
                raise ValueError(style)
            self.m.fact("programs", program_id=name, line=line)

    def environment(self) -> None:
        s = self.spec
        m = self.m
        if not (s.get("selects") or s.get("idms") or s.get("configuration") or s.get("special_names")):
            return
        m.cobol("ENVIRONMENT DIVISION.", area="A")
        if s.get("configuration") or s.get("special_names"):
            m.cobol("CONFIGURATION SECTION.", area="A")
            m.cobol("SOURCE-COMPUTER.    IBM-ZOS.", area="A")
            m.cobol("OBJECT-COMPUTER.    IBM-ZOS.", area="A")
        if s.get("special_names"):
            with m.horror(s.get("special_names_horror")):
                m.cobol("SPECIAL-NAMES.", area="A")
                for text in s["special_names"]:
                    m.cobol(text)
                m.append_to_last(".")
                m.phantom("units", name="SPECIAL-NAMES", why="an ENVIRONMENT DIVISION paragraph, not a procedure")
        if s.get("idms"):
            idms = s["idms"]
            with m.horror(idms.get("horror")):
                m.cobol("IDMS-CONTROL SECTION.", area="A")
                m.cobol(f"PROTOCOL.    MODE IS {idms['mode']} DEBUG", area="A")
                m.cobol("IDMS-RECORDS MANUAL.", indent=9)
                m.phantom("units", name="IDMS-CONTROL",
                          why="an ENVIRONMENT DIVISION section of the IDMS precompiler, not a procedure")
                m.phantom("units", name="PROTOCOL",
                          why="the IDMS-CONTROL SECTION's PROTOCOL paragraph, not a procedure")
        if s.get("selects"):
            m.cobol("INPUT-OUTPUT SECTION.", area="A")
            m.cobol("FILE-CONTROL.", area="A")
            for sel in s["selects"]:
                self.select(sel)
            if s.get("i_o_control"):
                with m.horror(s.get("special_names_horror")):
                    m.cobol("I-O-CONTROL.", area="A")
                    for text in s["i_o_control"]:
                        m.cobol(text)
                    m.append_to_last(".")
                    m.phantom("units", name="I-O-CONTROL", why="an ENVIRONMENT DIVISION paragraph, not a procedure")

    def select(self, sel: dict[str, Any]) -> None:
        m = self.m
        with m.horror(sel.get("horror")):
            if sel.get("assign_split"):
                # ASSIGN TO at the end of its line, the assignment-name on the next, both lines
                # carrying an identification tag in cols 73-80 (#4264)
                line = m.cobol(f"SELECT {sel['name']} ASSIGN TO", tag=sel["assign_split"])
                m.cobol(f"    {sel['assign']}", tag=sel["assign_split"])
            else:
                line = m.cobol(f"SELECT {sel['name']} ASSIGN TO {sel['assign']}")
            org = sel.get("org", "SEQUENTIAL")
            m.cobol(f"ORGANIZATION IS {org}", indent=4)
            if sel.get("access"):
                m.cobol(f"ACCESS MODE IS {sel['access']}", indent=4)
            if sel.get("record_key"):
                m.cobol(f"RECORD KEY IS {sel['record_key']}", indent=4)
            m.cobol(f"FILE STATUS IS {sel['status']}.", indent=4)
            fd = next((f for f in self.spec.get("fds", []) if f["fd"] == sel["name"]), None)
            rec = fd["record"] if fd else {}
            fd_copies = [rec["copy_only"]["member"]] if "copy_only" in rec else [c["member"] for c in rec.get("copy", [])]
            m.fact("file_control", select=sel["name"], assign=sel["assign"], organization=org,
                   access_mode=sel.get("access"), record_key=sel.get("record_key"), file_status=sel["status"],
                   fd_copies=fd_copies, line=line, **self.prog())

    def data(self) -> None:
        s = self.spec
        m = self.m
        if not (s.get("idms") or s.get("fds") or s.get("ws") or s.get("linkage")):
            return
        with m.horror(s.get("data_header_horror")):
            m.cobol(s.get("data_header", "DATA DIVISION") + ".", area="A")
        dw = DataWriter(m, self.resolve)
        if s.get("idms"):
            with m.horror(s["idms"].get("horror")):
                m.cobol("SCHEMA SECTION.", area="A")
                m.cobol(f"DB {s['idms']['subschema']} WITHIN {s['idms']['schema']}.", area="A")
                m.phantom("units", name="SCHEMA",
                          why="the IDMS SCHEMA SECTION of the DATA DIVISION, not a procedure")
        if s.get("fds"):
            m.cobol("FILE SECTION.", area="A")
            for fd in s["fds"]:
                m.cobol(f"FD  {fd['fd']}", area="A")
                m.cobol("RECORDING MODE IS F.")
                self.records([fd["record"]], "FILE", dw)
        first_fact = len(m.facts.get("data_items", []))
        for sec, key in (("WORKING-STORAGE", "ws"), ("LINKAGE", "linkage")):
            if s.get(key):
                m.cobol(f"{sec} SECTION.", area="A")
                self.records(s[key], sec, dw)
        self.expose_last_entry(first_fact)

    def expose_last_entry(self, first_fact: int) -> None:
        """#4329: the engine reads the last DATA DIVISION entry's USAGE past its period, into
        the PROCEDURE DIVISION. The last entry (and its record's layout) can only pass once
        that is fixed, unless the entry codes a USAGE of its own: mark it `depends_on`."""
        items = self.m.facts.get("data_items", [])[first_fact:]
        if not items:
            return
        last = items[-1]
        if last.get("usage") or last.get("horror") == "H-0009":
            return
        last.setdefault("depends_on", ["H-0009"])
        layouts = self.m.facts.get("layouts", [])
        if layouts and layouts[-1].get("horror") != "H-0009":
            layouts[-1].setdefault("depends_on", ["H-0009"])

    def records(self, items: list[Item], section: str, dw: DataWriter) -> None:
        prev: Optional[tuple[int, int]] = None  # (data_items index, layouts index) of the last 01 written
        for it in items:
            if "lvl" not in it:  # a bare COPY or EXEC SQL INCLUDE
                if "copy_only" in it and prev is not None and it.get("horror") != "H-0010":
                    # #4330: the engine folds a bare COPY into the 01 above it; that 01 can only
                    # pass once H-0010 is fixed
                    for ch, idx in zip(("data_items", "layouts"), prev):  # noqa: B905 -- equal lengths; 3.9
                        f = self.m.facts[ch][idx]
                        if f.get("horror") != "H-0010":
                            f.setdefault("depends_on", ["H-0010"])
                dw.items([it], section)
                prev = None
                continue
            for x in [it, *it.get("kids", [])]:
                if x.get("value") and (x.get("pic") or "").startswith("X") and x["value"].startswith("'"):
                    self.idents[x["name"]] = x["value"].strip("'")
            start = self.m.line_no
            dw.items([it], section)
            if it.get("lvl") == 1:
                first_item = next(i for i, f in enumerate(self.m.facts["data_items"]) if f["line"] == start)
                with self.m.horror(it.get("horror")):
                    extra = {"depends_on": it["depends_on"]} if it.get("depends_on") else {}
                    self.m.fact("layouts", **layout(it, self.m.path, self.resolve, start), **extra)
                prev = (first_item, len(self.m.facts["layouts"]) - 1)

    # ------------------------------------------------------------ procedure
    def procedure(self) -> None:
        s = self.spec
        using = s.get("using")
        header = s.get("procedure_header", "PROCEDURE DIVISION")
        with self.m.horror(s.get("procedure_header_horror")):
            pline = self.m.cobol(header + (f" USING {' '.join(using)}" if using else "") + ".", area="A")
        self.m.fact("entry_points", kind="PROCEDURE", program=s["program_id"],
                    params=list(using) if using else [], line=pline)
        if s.get("mainline"):
            with self.m.horror(s.get("mainline_horror")):
                start = self.m.line_no
                self.unit = None
                self.stmts(s["mainline"], 0)
                self.m.append_to_last(".")
                self.m.fact("units", name=None, kind="mainline", section=None, start_line=start,
                            end_line=len(self.m.lines), **self.prog())
        current_section: Optional[dict[str, Any]] = None
        for u in s["units"]:
            with self.m.horror(u.get("horror")):
                self.tag = u.get("tag")
                self.unit = u["name"]
                if u["kind"] == "section":
                    start = self.line(f"{u['name']} SECTION.", area="A", seq=u.get("seq"))
                    stmts = u["stmts"]
                elif u.get("header") == "period-next-line":
                    start = self.line(u["name"], area="A", seq=u.get("seq"))
                    self.line(".")
                    stmts = u["stmts"]
                elif u.get("header") == "inline":
                    first, *rest = u["stmts"]
                    if first["op"] != "raw" or len(first["lines"]) != 1:
                        raise ValueError(f"{self.m.path}: an inline header takes one raw statement")
                    start = self.line(f"{u['name']}. {first['lines'][0]}", area="A", seq=u.get("seq"))
                    with self.m.horror(first.get("horror")):
                        self.moves(first["lines"][0], start)
                    stmts = rest
                else:
                    start = self.line(f"{u['name']}.", area="A", seq=u.get("seq"))
                    stmts = u["stmts"]
                if self.m.free and len(u["name"]) > 7 and u["name"][6] == "-":
                    # free format: a hyphen where a fixed-format line has its indicator area
                    self.m.phantom("units", name=u["name"][7:],
                                   why=f"{u['name']} is one paragraph-name; free format has no column 7")
                if stmts:
                    self.stmts(stmts, 0)
                if u["stmts"]:
                    self.m.append_to_last(".")
                fact = self.m.fact("units", name=u["name"], kind=u["kind"],
                                   section=current_section["name"] if current_section and u["kind"] != "section" else None,
                                   start_line=start, end_line=len(self.m.lines), **self.prog())
                if u.get("dead"):
                    self.m.fact("dead", kind="paragraph", name=u["name"], line=start, why=u["dead"], **self.prog())
                if u["kind"] == "section":
                    if current_section is not None:
                        current_section["span_end"] = start - 1
                    current_section = fact
                self.tag = None
                if u.get("blank_after"):
                    self.m.blank()
        if current_section is not None:
            current_section["span_end"] = last_code_line(self.m)
        self.check_dead(s)

    def check_dead(self, s: dict[str, Any]) -> None:
        """A paragraph declared dead must be: no PERFORM / GO TO of this program names it (as a
        target or inside a THRU range), and the unit before it ends in an unconditional GOBACK,
        STOP RUN or GO TO, or is dead itself (Language Reference, "Procedures": statements run
        in the order written unless a statement transfers control)."""
        names = [u["name"] for u in s["units"]]
        targets: set = set()
        gotos = {e["target"] for e in self.m.facts.get("edges", []) if e["kind"] == "goto"
                 and e.get("program", s["program_id"]) == s["program_id"]}
        for e in self.m.facts.get("edges", []):
            if e.get("program", s["program_id"]) != s["program_id"] or e["kind"] not in ("perform", "goto"):
                continue
            if e["target"] in names:
                lo = names.index(e["target"])
                hi = names.index(e["thru"]) if e.get("thru") in names else lo
                targets.update(names[lo:hi + 1])
        def ends(stmts: list[Stmt]) -> bool:
            last = stmts[-1] if stmts else None
            return last is not None and (last["op"] == "goto" or (
                last["op"] == "raw" and last["lines"][-1].strip().upper() in ("GOBACK", "STOP RUN")))

        falls = not (s.get("mainline") and ends(s["mainline"]))  # control can run into this unit
        for u in s["units"]:
            if u.get("dead") and (u["kind"] != "paragraph" or u["name"] in targets or falls):
                raise ValueError(f"{self.m.path}: {u['name']} is declared dead but is reachable")
            # a unit entered by falling or by GO TO runs on into the next; one entered only by
            # PERFORM returns at its end
            falls = (falls or u["name"] in gotos) and not ends(u["stmts"])

    def stmts(self, stmts: list[Stmt], indent: int) -> None:
        for st in stmts:
            with self.m.horror(st.get("horror")):
                getattr(self, "op_" + st["op"])(st, indent)

    def op_raw(self, st: Stmt, indent: int) -> None:
        for text in st["lines"]:
            line = self.line(text, indent)
            self.moves(text, line)

    def moves(self, text: str, line: int) -> None:
        for row in cobol_moves(text, line):
            self.m.fact("data_moves", **row)

    def op_comment(self, st: Stmt, indent: int) -> None:
        for text in st["lines"]:
            self.m.cobol(" " * (indent + 4) + text, area="A", indicator="*")
        if st.get("perform"):
            self.m.phantom("edges", kind="perform", **{"from": self.unit}, target=st["perform"],
                           why="a PERFORM in a comment line (indicator *) is not a statement")
        if st["call"]:
            self.m.phantom("call_sites", verb="CALL", operand=st["call"],
                           why="a CALL in a comment line (indicator *) is not a statement")
            self.m.phantom("edges", kind="call", **{"from": self.unit}, target=st["call"],
                           why="a CALL in a comment line (indicator *) is not a statement")

    def op_perform(self, st: Stmt, indent: int) -> None:
        tail = ""
        if st["thru"]:
            tail += f" THRU {st['thru']}"
        if st["times"]:
            tail += f" {st['times']} TIMES"
        if st["until"]:
            tail += (f" WITH TEST {st['test']}" if st["test"] else "") + f" UNTIL {st['until']}"
        if st["split"]:
            line = self.line("PERFORM", indent)
            seq = self.m.seq_of(self.m.line_no)
            self.line(f"    {st['target']}{tail}", indent)
            if seq:
                self.m.phantom("edges", kind="perform", **{"from": self.unit}, target=seq,
                               why=f"the sequence number of the line after a split PERFORM, not {st['target']}")
        else:
            line = self.line(f"PERFORM {st['target']}{tail}", indent)
        extra = {"thru": st["thru"]} if st["thru"] else {}
        self.edge("perform", st["target"], line, **extra)

    def op_perform_inline(self, st: Stmt, indent: int) -> None:
        line = self.line(f"PERFORM {st['header']}", indent)
        first = st["header"].split()[0]
        self.m.phantom("edges", kind="perform", **{"from": self.unit}, target=first,
                       why=f"an inline PERFORM (line {line}) names no procedure; {first} is part of its header")
        self.stmts(st["body"], indent + 3)
        self.line("END-PERFORM", indent)

    def op_goto(self, st: Stmt, indent: int) -> None:
        if st["split"]:
            line = self.line("GO TO", indent)
            seq = self.m.seq_of(self.m.line_no)
            self.line(f"    {st['target']}", indent)
            if seq:
                self.m.phantom("edges", kind="goto", **{"from": self.unit}, target=seq,
                               why=f"the sequence number of the line after a split GO TO, not {st['target']}")
        else:
            line = self.line(f"GO TO {st['target']}", indent)
        self.edge("goto", st["target"], line)

    def op_call(self, st: Stmt, indent: int) -> None:
        operand = st["ident"] or st["target"]
        written = st["ident"] or f"'{st['target']}'"
        using = f" USING {' '.join(st['using'])}" if st["using"] else ""
        if st["split"]:
            line = self.line("CALL", indent)
            seq = self.m.seq_of(self.m.line_no)
            self.line(f"    {written}{using}", indent)
            if seq:
                self.m.phantom("edges", kind="call", **{"from": self.unit}, target=seq,
                               why=f"the sequence number of the line after a split CALL, not {operand}")
        else:
            line = self.line(f"CALL {written}{using}", indent)
        form = "identifier" if st["ident"] else "literal"
        if st["ident"] and self.idents.get(st["ident"]) != st["target"]:
            raise ValueError(f"{self.m.path}: CALL {st['ident']}: no VALUE '{st['target']}' in the program")
        self.edge("call", operand, line, form=form)
        self.m.fact("call_sites", verb="CALL", form=form, operand=operand, target=st["target"], line=line,
                    resolves_to=self.program_paths.get(st["target"]))

    def op_if(self, st: Stmt, indent: int) -> None:
        self.line(f"IF {st['cond']}", indent)
        self.stmts(st["then"], indent + 3)
        if st["else_"]:
            self.line("ELSE", indent)
            self.stmts(st["else_"], indent + 3)
        self.line("END-IF", indent)

    def op_read(self, st: Stmt, indent: int) -> None:
        line = self.line(f"READ {st['file']}" + (f" INTO {st['into']}" if st["into"] else ""), indent)
        if st["into"]:
            self.m.fact("data_moves", verb="READ", source=st["file"], source_kind="file", target=st["into"],
                        corresponding=False, source_refmod=False, target_refmod=False, source_refmod_text=None,
                        target_refmod_text=None, line=line)
        self.line("AT END", indent + 3)
        self.stmts(st["at_end"], indent + 6)
        if st["not_at_end"]:
            self.line("NOT AT END", indent + 3)
            self.stmts(st["not_at_end"], indent + 6)
        self.line("END-READ", indent)

    def op_exit_perform(self, st: Stmt, indent: int) -> None:
        line = self.line("EXIT PERFORM" + (" CYCLE" if st["cycle"] else ""), indent)
        self.exit_performs.append((line, self.unit, self.m._horror))

    def op_sql(self, st: Stmt, indent: int) -> None:
        if len(st["lines"]) == 1 and len(st["lines"][0]) < 40:
            line = self.line(f"EXEC SQL {st['lines'][0]} END-EXEC", indent)
        else:
            line = self.line("EXEC SQL", indent)
            for text in st["lines"]:
                self.line(text, indent + 4)
            self.line("END-EXEC", indent)
        self.m.fact("sql_statements", verb=st["verb"], table=st["table"], access=st["access"], line=line,
                    **({"procedure": st["proc"]} if st["proc"] else {}))
        if st["proc"]:
            first = st["proc"].split(".")[0]
            why = f"EXEC SQL CALL {st['proc']} invokes a Db2 stored procedure, not a COBOL program"
            self.m.phantom("call_sites", verb="CALL", operand=first, line=line, why=why)
            self.m.phantom("edges", kind="call", **{"from": self.unit}, target=first, why=why)

    def op_cics(self, st: Stmt, indent: int) -> None:
        cmd = st["lines"]
        if st["own_line"]:
            line = self.line("EXEC CICS", indent)
            for text in cmd:
                self.line(text, indent + 4)
            self.line("END-EXEC", indent)
        else:
            line = self.line(f"EXEC CICS {cmd[0]}", indent)
            for text in cmd[1:]:
                self.line(text, indent + 10)
            self.line("END-EXEC", indent)
        if st["verb"]:
            self.m.fact("call_sites", verb=st["verb"], form="literal", operand=st["operand"], target=st["operand"],
                        line=line, resolves_to=self.program_paths.get(st["operand"]) if st["verb"] in ("LINK", "XCTL") else None)
        if st.get("resource"):
            r = st["resource"]
            self.m.fact("cics_resources", verb=r["verb"], kind=r["kind"], name=r["name"],
                        qualifier=r.get("qualifier"), record=r.get("record"), access=r["access"], line=line)

    def resolve_exit_performs(self) -> None:
        """EXIT PERFORM is not a PERFORM: whatever token follows it must not become a callee."""
        for line, unit, horror in self.exit_performs:
            text = self.m.lines[line - 1][7:72].split()
            follows = []
            if len(text) > 2:
                follows.append(text[2])
            else:
                at = next(i for i in range(line, len(self.m.lines))
                          if len(self.m.lines[i]) > 6 and self.m.lines[i][6] not in "*/")
                follows.append(self.m.lines[at][7:72].split()[0])
                if self.m.numbered:
                    # the next token in the raw text is that line's sequence number
                    follows.append(self.m.lines[at][:6])
            for nxt in follows:
                with self.m.horror(horror):
                    self.m.phantom("edges", kind="perform", **{"from": unit}, target=nxt.rstrip("."),
                                   why=f"EXIT PERFORM (line {line}) is not a PERFORM; {nxt.rstrip('.')} follows it")


def repr_name(pid: str, spec: dict[str, Any]) -> str:
    return f"'{pid}'" if spec.get("program_id_style") == "quoted" else pid


def last_code_line(m: Member) -> int:
    for i in range(len(m.lines), 0, -1):
        ln = m.lines[i - 1]
        if len(ln) > 7 and ln[6] not in "*/" and ln[7:72].strip():
            return i
    return len(m.lines)


def all_programs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Every program a member's spec holds: itself, its nested programs, its siblings."""
    out = [spec]
    for n in spec.get("nested", []):
        out += all_programs(n)
    for sib in spec.get("siblings", []):
        out += all_programs(sib)
    return out


def write_program(m: Member, spec: dict[str, Any], resolve: Resolver, program_paths: dict[str, str]) -> None:
    multi = bool(spec.get("nested") or spec.get("siblings"))
    if spec.get("free"):
        m.raw("       >>SOURCE FORMAT FREE")
    with m.horror(spec.get("member_horror")):
        ProgramWriter(m, spec, resolve, program_paths, multi).write()
        for sib in spec.get("siblings", []):
            ProgramWriter(m, sib, resolve, program_paths, True).write()
    m.compile = {"status": spec.get("compile", COMPILED)}
    if spec.get("compile_reason"):
        m.compile["reason"] = spec["compile_reason"]
    if spec.get("compile_check"):
        m.compile["check_variant"], m.compile["check_note"] = spec["compile_check"]


def write_copybook(m: Member, spec: dict[str, Any], resolve: Resolver) -> None:
    for c in spec.get("header", []):
        m.comment(c)
    with m.horror(spec.get("horror")):
        DataWriter(m, resolve).items(spec["items"], None)
    m.compile = {"status": "copybook"}
