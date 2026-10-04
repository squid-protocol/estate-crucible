"""PL/I members: an external procedure with its declarations and internal procedures.

Units follow the same flat model as COBOL (SPEC 3): the external procedure's unit is its
own statements, from `NAME: PROC` to its last statement before the first internal
procedure (`span_end` is its END); an internal procedure runs from `NAME: PROC` to its END.
"""

from __future__ import annotations

from typing import Any, Optional

from .model import Member

PliStmt = dict[str, Any]


def pcall(target: str, *args: str, external: bool = False, horror: Optional[str] = None) -> PliStmt:
    """CALL target(args); `external` marks a separately compiled program (a declared ENTRY)."""
    return {"op": "call", "target": target, "args": list(args), "external": external, "horror": horror}


def praw(*lines: str, horror: Optional[str] = None) -> PliStmt:
    return {"op": "raw", "lines": list(lines), "horror": horror}


def pif(cond: str, then: list[PliStmt], else_: Optional[list[PliStmt]] = None, *, horror: Optional[str] = None) -> PliStmt:
    """IF cond THEN <one statement>; [ELSE <one statement>;] -- each branch is one statement."""
    return {"op": "if", "cond": cond, "then": then, "else_": else_, "horror": horror}


class PliWriter:
    def __init__(self, m: Member, spec: dict[str, Any], program_paths: dict[str, str]) -> None:
        self.m = m
        self.spec = spec
        self.program_paths = program_paths
        self.unit = spec["proc"]

    def line(self, text: str, indent: int = 0) -> int:
        return self.m.raw((" " + " " * indent + text).rstrip())

    def write(self) -> None:
        s = self.spec
        m = self.m
        for c in s.get("comments", []):
            self.line(f"/* {c:<64} */")
        params = s.get("params", [])
        head = f"{s['proc']}: PROC" + (f"({', '.join(params)})" if params else "")
        head += f" OPTIONS({s['options']});" if s.get("options") else ";"
        with m.horror(s.get("horror")):
            start = self.line(head)
            m.fact("entry_points", kind="PROCEDURE", program=s["proc"], params=params, line=start)
            if s.get("options") and "MAIN" in s["options"]:
                m.fact("programs", program_id=s["proc"], line=start)
            for group in s.get("decls", []):
                self.declare(group)
            self.stmts(s["stmts"], 2)
            own_end = len(m.lines)
            outer = m.fact("units", name=s["proc"], kind="procedure", section=None, start_line=start,
                           end_line=own_end)
        for ip in s.get("internal", []):
            with m.horror(ip.get("horror")):
                self.line("")
                self.unit = ip["name"]
                istart = self.line(f"{ip['name']}: PROC;")
                self.stmts(ip["stmts"], 2)
                iend = self.line(f"END {ip['name']};")
                m.fact("units", name=ip["name"], kind="procedure", section=None, start_line=istart, end_line=iend)
        outer["span_end"] = self.line(f"END {s['proc']};")
        m.compile = {"status": "ibm-only", "reason": "PL/I: the check has no PL/I compiler (IBM Enterprise PL/I)"}

    def declare(self, group: list[tuple[Any, str, str]]) -> None:
        """One DECLARE: a scalar `[(1, NAME, attrs)]`, an entry `[("ENTRY", NAME, "")]`
        (no data item), or a structure `[(1, NAME, ""), (2, FIELD, attrs), ...]`."""
        if group[0][0] == "ENTRY":
            self.line(f"DCL {group[0][1]} ENTRY;", 2)
            return
        if len(group) == 1:
            lvl, name, attrs = group[0]
            dline = self.line(f"DCL {name} {attrs};", 2)
            self.m.fact("data_items", level=1, name=name, pic=None, usage=attrs, occurs=None, redefines=None,
                        value=None, section=None, line=dline)
            return
        for i, (lvl, name, attrs) in enumerate(group):
            end = ";" if i == len(group) - 1 else ","
            text = f"DCL {lvl} {name}" if i == 0 else f"{' ' * (2 * lvl)}{lvl} {name:<12} {attrs}"
            dline = self.line(text.rstrip() + end, 2)
            self.m.fact("data_items", level=lvl, name=name, pic=None, usage=attrs or None, occurs=None,
                        redefines=None, value=None, section=None, line=dline)

    def stmts(self, stmts: list[PliStmt], indent: int) -> None:
        for st in stmts:
            with self.m.horror(st.get("horror")):
                getattr(self, "op_" + st["op"])(st, indent)

    def op_raw(self, st: PliStmt, indent: int) -> None:
        from .moves import pli_moves

        for text in st["lines"]:
            line = self.line(text, indent)
            for row in pli_moves(text, line):
                self.m.fact("data_moves", **row)

    def op_call(self, st: PliStmt, indent: int) -> None:
        args = f"({', '.join(st['args'])})" if st["args"] else ""
        line = self.line(f"CALL {st['target']}{args};", indent)
        self.m.fact("edges", kind="call", **{"from": self.unit}, target=st["target"], line=line, form="literal")
        if st["external"]:
            self.m.fact("call_sites", verb="CALL", form="literal", operand=st["target"], target=st["target"],
                        line=line, resolves_to=self.program_paths.get(st["target"]))

    def op_if(self, st: PliStmt, indent: int) -> None:
        self.line(f"IF {st['cond']} THEN", indent)
        self.stmts(st["then"], indent + 2)
        if st["else_"]:
            els = st["else_"]
            if len(els) == 1 and els[0]["op"] == "raw" and len(els[0]["lines"]) == 1:
                with self.m.horror(els[0].get("horror")):
                    self.line(f"ELSE {els[0]['lines'][0]}", indent)
                    if "=" in els[0]["lines"][0]:
                        raise ValueError("an assignment as an ELSE unit is not modelled")
            else:
                self.line("ELSE", indent)
                self.stmts(els, indent + 2)


def write_pli(m: Member, spec: dict[str, Any], program_paths: dict[str, str]) -> None:
    PliWriter(m, spec, program_paths).write()
