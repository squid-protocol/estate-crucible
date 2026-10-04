"""The data_moves facts of the statements the generator writes.

Apps write most procedure statements as `raw(...)` text. That text is the generator's own data
(not the rendered member), and this module reads it with a deliberately small grammar, the
statement forms the apps use:

    MOVE [CORRESPONDING] src TO t1 [t2 ...]      ADD a [b ...] TO t        SUBTRACT a FROM t
    COMPUTE t [ROUNDED] = expr                   INITIALIZE t1 [t2 ...]    WRITE r FROM s
    PL/I: target = expr;

Every other verb moves no data (DISPLAY, SET, OPEN, CLOSE, GOBACK, ...). A data-moving verb in
a form this grammar does not know raises, so an app cannot plant a move the key would miss.
The blind spot is the usual one: this reading is only as right as the grammar.

One row per source -> target pair, as GitGalaxy's data_move_data defines them: `source` as
written (a name with its qualifiers, a literal, a figurative constant, `FUNCTION NAME`), its
`source_kind`, the `target`, `corresponding`, and any reference modification (`1:4`) on
either side. A subscript is not a source and is dropped.
"""

from __future__ import annotations

import re
from typing import Any, Optional

FIGURATIVE = {"ZERO", "ZEROS", "ZEROES", "SPACE", "SPACES", "LOW-VALUE", "LOW-VALUES", "HIGH-VALUE",
              "HIGH-VALUES", "QUOTE", "QUOTES", "NULL", "NULLS"}
NOT_MOVES = {"DISPLAY", "SET", "OPEN", "CLOSE", "GOBACK", "STOP", "EXIT", "CONTINUE", "BIND", "READY", "FINISH",
             "OBTAIN", "DC", "PERFORM", "CALL", "IF", "ELSE", "END-IF", "READ", "PUT", "RETURN;", "RETURN", "CHECK"}
MOVING = {"MOVE", "ADD", "SUBTRACT", "COMPUTE", "INITIALIZE", "WRITE", "REWRITE", "MULTIPLY", "DIVIDE", "STRING",
          "UNSTRING", "ACCEPT"}

# an operand: a literal, ALL + literal, FUNCTION name [(refmod)], or a name [OF q]... [(sub | refmod)]
_LIT = r"(?:[GNX]?'[^']*'|[GNX]?\"[^\"]*\"|[+-]?\d+(?:[.,]\d+)?)"
_NAME = r"[^\s().,'\"=*/+]+(?:-[^\s().,'\"=*/+]+)*"
_OPERAND = re.compile(
    rf"(?P<all>ALL\s+{_LIT})|(?P<lit>{_LIT})|(?P<func>FUNCTION\s+{_NAME})(?:\s*\((?P<frm>[^()]*:[^()]*)\))?"
    rf"|(?P<name>{_NAME}(?:\s+(?:OF|IN)\s+{_NAME})*)(?:\s*\((?P<paren>[^()]*)\))?",
    re.I,
)


def _operand(text: str) -> tuple[Optional[str], Optional[str], bool, Optional[str]]:
    """(operand as written, kind, refmod?, refmod text) of one operand."""
    m = _OPERAND.fullmatch(text.strip())
    if not m:
        raise ValueError(f"moves: cannot read operand {text!r}")
    if m.group("all"):
        return " ".join(m.group("all").split()), "figurative", False, None
    if m.group("lit"):
        return m.group("lit"), "literal", False, None
    if m.group("func"):
        frm = m.group("frm")
        return " ".join(m.group("func").split()).upper(), "function", bool(frm), frm.replace(" ", "") if frm else None
    name = " ".join(m.group("name").split())
    paren = m.group("paren")
    refmod = paren is not None and ":" in paren
    if name.upper() in FIGURATIVE:
        return name.upper(), "figurative", False, None
    return name, "item", refmod, paren.replace(" ", "") if refmod and paren else None


def _split_operands(text: str) -> list[str]:
    """Operands separated by blanks (or commas), keeping `X OF Y`, `(..)` and literals whole."""
    out: list[str] = []
    for m in _OPERAND.finditer(text):
        if m.group(0).strip():
            out.append(m.group(0))
    return out


def _split_kw(text: str, kw: str) -> list[str]:
    """Split at the first ` kw ` that is outside a literal."""
    masked = re.sub(r"'[^']*'|\"[^\"]*\"", lambda m: "x" * len(m.group(0)), text)
    m = re.search(rf"\s+{kw}\s+", masked, re.I)
    return [text] if not m else [text[: m.start()], text[m.end():]]


def _row(verb: str, source: Optional[str], kind: Optional[str], target_text: str, line: int,
         corresponding: bool = False, s_ref: bool = False, s_ref_text: Optional[str] = None) -> dict[str, Any]:
    target, _, t_ref, t_ref_text = _operand(target_text)
    return {"verb": verb, "source": source, "source_kind": kind, "target": target, "corresponding": corresponding,
            "source_refmod": s_ref, "target_refmod": t_ref, "source_refmod_text": s_ref_text,
            "target_refmod_text": t_ref_text, "line": line}


def cobol_moves(stmt: str, line: int) -> list[dict[str, Any]]:
    text = " ".join(stmt.split()).rstrip(".")
    if not text:
        return []
    verb = text.split()[0].upper()
    if verb not in MOVING:
        if verb in NOT_MOVES or verb.startswith(("END-", "*")):
            return []
        if re.match(r"(AT|NOT|WHEN|ELSE)\b", verb):
            return []
        return []
    rest = text[len(verb):].strip()
    if verb == "MOVE":
        corr = False
        m = re.match(r"(CORRESPONDING|CORR)\s+", rest, re.I)
        if m:
            corr, rest = True, rest[m.end():]
        src_text, tgts = _split_kw(rest, "TO")
        src, kind, s_ref, s_ref_text = _operand(src_text)
        return [_row("MOVE", src, kind, t, line, corr, s_ref, s_ref_text) for t in _split_operands(tgts)]
    if verb in ("ADD", "SUBTRACT"):
        word = "TO" if verb == "ADD" else "FROM"
        parts = _split_kw(rest, word)
        if len(parts) != 2 or re.search(r"\bGIVING\b", rest, re.I):
            raise ValueError(f"moves: {verb} form not modelled: {stmt!r}")
        rows = []
        for s in _split_operands(parts[0]):
            src, kind, s_ref, s_ref_text = _operand(s)
            rows += [_row(verb, src, kind, t, line, False, s_ref, s_ref_text) for t in _split_operands(parts[1])]
        return rows
    if verb == "COMPUTE":
        lhs, _, expr = rest.partition("=")
        targets = [t for t in _split_operands(lhs) if t.upper() != "ROUNDED"]
        rows = []
        for tok in _split_operands(expr):
            src, kind, s_ref, s_ref_text = _operand(tok)
            if kind not in ("item", "function"):
                continue
            rows += [_row("COMPUTE", src, kind, t, line, False, s_ref, s_ref_text) for t in targets]
        return rows
    if verb == "INITIALIZE":
        return [_row("INITIALIZE", None, None, t, line) for t in _split_operands(rest)]
    if verb in ("WRITE", "REWRITE"):
        if not re.search(r"\sFROM\s", rest, re.I):
            return []
        rec, src_text = _split_kw(rest, "FROM")
        src, kind, s_ref, s_ref_text = _operand(src_text)
        return [_row(verb, src, kind, rec, line, False, s_ref, s_ref_text)]
    raise ValueError(f"moves: {verb} not modelled: {stmt!r}")


def pli_moves(stmt: str, line: int) -> list[dict[str, Any]]:
    text = stmt.strip().rstrip(";").strip()
    m = re.fullmatch(r"([^\W\d][\w]*)\s*=\s*(.+)", text)
    if not m or text.upper().startswith(("IF ", "DCL ")):
        return []
    rows = []
    for tok in re.findall(r"'[^']*'|[^\W\d]\w*|\d+(?:\.\d+)?", m.group(2)):
        kind = "literal" if tok[0] in "'0123456789" else "item"
        rows.append(_row("ASSIGN", tok, kind, m.group(1), line))
    return rows
