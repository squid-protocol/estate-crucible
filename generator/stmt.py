"""The PROCEDURE DIVISION statement DSL. App definitions build programs out of these; each
constructor returns a plain dict, and cobol.py renders it and records its facts."""

from __future__ import annotations

from typing import Any, Optional

Stmt = dict[str, Any]


def _s(op: str, horror: Optional[str], **kw: Any) -> Stmt:
    return {"op": op, "horror": horror, **kw}


def raw(*lines: str, horror: Optional[str] = None) -> Stmt:
    """Statements that carry no fact the key scores (MOVE, ADD, DISPLAY, OPEN, ...)."""
    return _s("raw", horror, lines=list(lines))


def perform(target: str, *, thru: Optional[str] = None, until: Optional[str] = None, times: Optional[str] = None,
            test: Optional[str] = None, split: bool = False, horror: Optional[str] = None) -> Stmt:
    """Out-of-line PERFORM procedure-name-1 [THRU procedure-name-2] [n TIMES | [WITH TEST x] UNTIL c].
    `split` puts the procedure-name on the next line."""
    return _s("perform", horror, target=target, thru=thru, until=until, times=times, test=test, split=split)


def perform_inline(header: str, body: list[Stmt], *, horror: Optional[str] = None) -> Stmt:
    """Inline PERFORM: `PERFORM <header>` ... END-PERFORM. No procedure-name, so no edge; the
    first word of the header is declared a phantom callee."""
    return _s("perform_inline", horror, header=header, body=body)


def goto(target: str, *, split: bool = False, horror: Optional[str] = None) -> Stmt:
    return _s("goto", horror, target=target, split=split)


def call(target: str, *, ident: Optional[str] = None, using: Optional[list[str]] = None, split: bool = False,
         horror: Optional[str] = None) -> Stmt:
    """CALL 'target' or, with `ident`, CALL ident (whose VALUE is `target`)."""
    return _s("call", horror, target=target, ident=ident, using=using or [], split=split)


def if_(cond: str, then: list[Stmt], else_: Optional[list[Stmt]] = None, *, horror: Optional[str] = None) -> Stmt:
    return _s("if", horror, cond=cond, then=then, else_=else_)


def read(file: str, *, into: Optional[str] = None, at_end: list[Stmt], not_at_end: Optional[list[Stmt]] = None,
         horror: Optional[str] = None) -> Stmt:
    return _s("read", horror, file=file, into=into, at_end=at_end, not_at_end=not_at_end)


def goback(horror: Optional[str] = None) -> Stmt:
    return raw("GOBACK", horror=horror)


def stop_run(horror: Optional[str] = None) -> Stmt:
    return raw("STOP RUN", horror=horror)


def exit_perform(*, cycle: bool = False, horror: Optional[str] = None) -> Stmt:
    return _s("exit_perform", horror, cycle=cycle)


def exit_para() -> Stmt:
    return raw("EXIT")


def sql(*lines: str, verb: str, table: Optional[str] = None, access: Optional[str] = None,
        proc: Optional[str] = None, horror: Optional[str] = None) -> Stmt:
    """EXEC SQL <lines> END-EXEC. `proc` marks a CALL of a stored procedure (schema.name)."""
    return _s("sql", horror, lines=list(lines), verb=verb, table=table, access=access, proc=proc)


def cics(*lines: str, verb: Optional[str] = None, operand: Optional[str] = None, own_line: bool = False,
         resource: Optional[dict[str, Any]] = None, horror: Optional[str] = None) -> Stmt:
    """EXEC CICS <lines> END-EXEC. `verb` / `operand` record a call site (LINK, XCTL,
    RETURN TRANSID). `resource` records the CICS resource the command touches
    (cics_resources: verb, kind, name, qualifier, record, access). `own_line` writes EXEC
    CICS, the command and END-EXEC on three lines, so the command (e.g. RETURN) starts its line."""
    return _s("cics", horror, lines=list(lines), verb=verb, operand=operand, own_line=own_line, resource=resource)


def comment_code(*lines: str, call: Optional[str] = None, perform: Optional[str] = None,
                 horror: Optional[str] = None) -> Stmt:
    """Commented-out code (`*` in column 7). `call` names a program a commented CALL
    mentions, `perform` a procedure a commented PERFORM names: neither may become a call
    site or an edge."""
    return _s("comment", horror, lines=list(lines), call=call, perform=perform)


def para(name: str, *stmts: Stmt, horror: Optional[str] = None, tag: Optional[str] = None,
         header: str = "normal", blank_after: bool = False, seq: Optional[str] = None,
         dead: Optional[str] = None) -> dict[str, Any]:
    """A paragraph. `tag` writes a change tag in cols 73-80 of every line of it. `header`:
    normal, period-next-line (the name alone, the period on the next line) or inline (the
    first statement on the header line). `blank_after` writes an empty line after it (a
    numbered member keeps the sequence number there). `seq` overrides the header line's
    cols 1-6 (a change marker). `dead` says why nothing reaches the paragraph (no PERFORM or
    GO TO names it and the paragraph before it does not fall into it); the writer checks it."""
    return {"name": name, "kind": "paragraph", "stmts": list(stmts), "horror": horror, "tag": tag,
            "header": header, "blank_after": blank_after, "seq": seq, "dead": dead}


def section(name: str, *stmts: Stmt, horror: Optional[str] = None, blank_after: bool = False) -> dict[str, Any]:
    return {"name": name, "kind": "section", "stmts": list(stmts), "horror": horror, "tag": None,
            "header": "normal", "blank_after": blank_after, "seq": None}
