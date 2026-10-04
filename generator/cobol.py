"""Renders a COBOL program or copybook spec into a Member, recording its facts."""

from __future__ import annotations

from typing import Any, Callable, Optional

from .data import DataWriter, Item, layout
from .model import Member
from .stmt import Stmt

Resolver = Callable[[str], tuple[Optional[str], Optional[list[Item]]]]

# How the compile check treats a member (SPEC.md, "Validity"). The status is part of the key.
COMPILED = "compiled"  # cobc -std=ibm, as written
STUBBED = "compiled-stubbed"  # cobc -std=ibm after EXEC SQL / EXEC CICS are replaced by CONTINUE
IBM_ONLY = "ibm-only"  # not compiled; `reason` says why


class ProgramWriter:
    def __init__(self, m: Member, spec: dict[str, Any], resolve: Resolver,
                 program_paths: dict[str, str]) -> None:
        self.m = m
        self.spec = spec
        self.resolve = resolve
        self.program_paths = program_paths
        self.unit: Optional[str] = None
        self.tag: Optional[str] = None
        self.exit_performs: list[tuple[int, Optional[str], Optional[str]]] = []
        self.idents: dict[str, str] = {}

    # ------------------------------------------------------------ helpers
    def line(self, text: str, indent: int = 0, area: str = "B") -> int:
        return self.m.cobol(text, area=area, indent=indent, tag=self.tag)

    def edge(self, kind: str, target: str, line: int, **extra: Any) -> None:
        self.m.fact("edges", kind=kind, **{"from": self.unit}, target=target, line=line, **extra)

    # ------------------------------------------------------------ divisions
    def write(self) -> None:
        s = self.spec
        m = self.m
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
            else:
                raise ValueError(style)
            self.m.fact("programs", program_id=name, line=line)

    def environment(self) -> None:
        s = self.spec
        m = self.m
        if not (s.get("selects") or s.get("idms") or s.get("configuration")):
            return
        m.cobol("ENVIRONMENT DIVISION.", area="A")
        if s.get("configuration"):
            m.cobol("CONFIGURATION SECTION.", area="A")
            m.cobol("SOURCE-COMPUTER.    IBM-ZOS.", area="A")
            m.cobol("OBJECT-COMPUTER.    IBM-ZOS.", area="A")
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
                m.cobol(f"SELECT {sel['name']} ASSIGN TO {sel['assign']}")
                m.cobol(f"ORGANIZATION IS {sel.get('org', 'SEQUENTIAL')}", indent=4)
                m.cobol(f"FILE STATUS IS {sel['status']}.", indent=4)

    def data(self) -> None:
        s = self.spec
        m = self.m
        m.cobol("DATA DIVISION.", area="A")
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
        for sec, key in (("WORKING-STORAGE", "ws"), ("LINKAGE", "linkage")):
            if s.get(key):
                m.cobol(f"{sec} SECTION.", area="A")
                self.records(s[key], sec, dw)

    def records(self, items: list[Item], section: str, dw: DataWriter) -> None:
        for it in items:
            if it.get("value") and it.get("pic", "").startswith("X") and it["value"].startswith("'"):
                self.idents[it["name"]] = it["value"].strip("'")
            for kid in it.get("kids", []):
                if kid.get("value") and (kid.get("pic") or "").startswith("X") and kid["value"].startswith("'"):
                    self.idents[kid["name"]] = kid["value"].strip("'")
            start = self.m.line_no
            dw.items([it], section)
            if it.get("lvl") == 1:
                with self.m.horror(it.get("horror")):
                    self.m.fact("layouts", **layout(it, self.m.path, self.resolve, start))

    # ------------------------------------------------------------ procedure
    def procedure(self) -> None:
        s = self.spec
        using = s.get("using")
        self.m.cobol("PROCEDURE DIVISION" + (f" USING {' '.join(using)}" if using else "") + ".", area="A")
        if s.get("mainline"):
            with self.m.horror(s.get("mainline_horror")):
                start = self.m.line_no
                self.unit = None
                self.stmts(s["mainline"], 0)
                self.m.append_to_last(".")
                self.m.fact("units", name=None, kind="mainline", section=None, start_line=start,
                            end_line=len(self.m.lines))
        current_section: Optional[dict[str, Any]] = None
        for u in s["units"]:
            with self.m.horror(u.get("horror")):
                self.tag = u.get("tag")
                self.unit = u["name"]
                header = f"{u['name']} SECTION." if u["kind"] == "section" else f"{u['name']}."
                start = self.line(header, area="A")
                if u["stmts"]:
                    self.stmts(u["stmts"], 0)
                    self.m.append_to_last(".")
                fact = self.m.fact("units", name=u["name"], kind=u["kind"],
                                   section=current_section["name"] if current_section and u["kind"] != "section" else None,
                                   start_line=start, end_line=len(self.m.lines))
                if u["kind"] == "section":
                    if current_section is not None:
                        current_section["span_end"] = start - 1
                    current_section = fact
                self.tag = None
        if current_section is not None:
            current_section["span_end"] = len(self.m.lines)

    def stmts(self, stmts: list[Stmt], indent: int) -> None:
        for st in stmts:
            with self.m.horror(st.get("horror")):
                getattr(self, "op_" + st["op"])(st, indent)

    def op_raw(self, st: Stmt, indent: int) -> None:
        for text in st["lines"]:
            self.line(text, indent)

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
        self.line(f"READ {st['file']}" + (f" INTO {st['into']}" if st["into"] else ""), indent)
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


def write_program(m: Member, spec: dict[str, Any], resolve: Resolver, program_paths: dict[str, str]) -> None:
    ProgramWriter(m, spec, resolve, program_paths).write()
    m.compile = {"status": spec.get("compile", COMPILED)}
    if spec.get("compile_reason"):
        m.compile["reason"] = spec["compile_reason"]
    if spec.get("compile_check"):
        m.compile["check_variant"], m.compile["check_note"] = spec["compile_check"]


def write_copybook(m: Member, spec: dict[str, Any], resolve: Resolver) -> None:
    for c in spec.get("header", []):
        m.comment(c)
    DataWriter(m, resolve).items(spec["items"], None)
    m.compile = {"status": "copybook"}
