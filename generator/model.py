"""The member writer: one source member's lines and the facts recorded while writing them.

Every fact in the answer key is recorded here, at the moment the line that carries it is
emitted, by the code that emits it. Nothing reads the generated text back. That is the
whole point of the crucible, and also its blind spot: the key is only as right as the
writer's idea of what it wrote (see README, "Ground rules").
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Optional

# Fixed-format reference format (Enterprise COBOL Language Reference, "Reference format"):
# cols 1-6 sequence number area, col 7 indicator area, cols 8-11 Area A, cols 12-72 Area B,
# cols 73-80 the program-name identification area (here: change tags).
SEQ_WIDTH = 6
AREA_A_COL = 8
AREA_B_COL = 12
CODE_END_COL = 72

# Fact channels, in the order the key lists them. A channel is one kind of fact the engine
# is scored on; the scorer in gitgalaxy projects the engine's master DB onto these.
CHANNELS = (
    "programs",
    "units",
    "edges",
    "call_sites",
    "copies",
    "data_items",
    "layouts",
    "sql_statements",
    "sql_tables",
    "jcl_steps",
    "jcl_dds",
    "screen_fields",
    "csd_resources",
    "transactions",
    # phase 1 (#4317)
    "cics_resources",
    "jcl_datasets",
    "file_control",
    "entry_points",
    "file_edges",
)


class Member:
    """One member being written. `numbered` puts ISPF-style sequence numbers (NUMBER ON STD,
    step 100) in cols 1-6 of every line, as a member pulled from a PDS has them."""

    def __init__(
        self,
        path: str,
        language: str,
        *,
        app: Optional[str],
        library: str,
        numbered: bool = False,
        seq_step: int = 100,
        free: bool = False,
    ) -> None:
        self.path = path
        self.language = language
        self.app = app
        self.library = library
        self.numbered = numbered
        self.seq_step = seq_step
        # free-format source (>>SOURCE FORMAT FREE): no sequence or indicator area, no column 72
        self.free = free
        self.lines: list[str] = []
        self.facts: dict[str, list[dict[str, Any]]] = {}
        self.phantoms: list[dict[str, Any]] = []
        self.horrors: set[str] = set()
        self.compile: dict[str, Any] = {"status": "not-cobol"}
        # a member another member is generated from (a BMS symbolic map's mapset source)
        self.generated_from: Optional[str] = None
        self._horror: Optional[str] = None

    # ---------------------------------------------------------------- lines
    @property
    def line_no(self) -> int:
        """The number the next emitted line will get."""
        return len(self.lines) + 1

    def seq_of(self, line_no: int) -> str:
        return f"{line_no * self.seq_step:06d}" if self.numbered else ""

    def raw(self, text: str) -> int:
        """Emit a line exactly as given (JCL, BMS, CSD, or a deliberately odd COBOL line)."""
        self.lines.append(text)
        return len(self.lines)

    def cobol(self, text: str, *, area: str = "B", indent: int = 0, indicator: str = " ",
              tag: Optional[str] = None, pad: bool = False, seq: Optional[str] = None) -> int:
        """Emit one fixed-format COBOL line. `area` A starts at col 8, B at col 12 (+indent).
        `tag` fills cols 73-80; `pad` keeps the line blank-padded to col 72 (a member saved
        from ISPF with trailing blanks)."""
        lead = "" if area == "A" else " " * (AREA_B_COL - AREA_A_COL + indent)
        if self.free:
            if indicator == "*":
                self.lines.append((lead + "*> " + text).rstrip())
            else:
                self.lines.append((lead + text).rstrip())
            return len(self.lines)
        seq = (seq if seq is not None else self.seq_of(self.line_no)).ljust(SEQ_WIDTH)
        line = seq + indicator + lead + text
        if len(line) > CODE_END_COL:
            raise ValueError(f"{self.path}:{self.line_no}: past column 72: {line!r}")
        if tag is not None:
            if len(tag) > 8:
                raise ValueError(f"tag {tag!r} is longer than cols 73-80")
            line = line.ljust(CODE_END_COL) + tag
        elif pad:
            line = line.ljust(CODE_END_COL)
        else:
            line = line.rstrip()
        self.lines.append(line)
        return len(self.lines)

    def blank(self) -> int:
        """An empty line. A numbered member keeps the sequence number on it, as ISPF does."""
        return self.raw(self.seq_of(self.line_no))

    def comment(self, text: str = "") -> int:
        return self.cobol(text, area="A", indicator="*")

    def append_to_last(self, suffix: str) -> None:
        """Append to the code of the last line (a closing period), keeping a change tag in place."""
        last = self.lines[-1]
        code, tag = (last[:CODE_END_COL].rstrip(), last[CODE_END_COL:]) if len(last) > CODE_END_COL else (last, "")
        code += suffix
        if len(code) > CODE_END_COL:
            raise ValueError(f"{self.path}:{len(self.lines)}: past column 72 after {suffix!r}")
        self.lines[-1] = code.ljust(CODE_END_COL) + tag if tag else code

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    # ---------------------------------------------------------------- facts
    @contextmanager
    def horror(self, horror_id: Optional[str]) -> Iterator[None]:
        """Tag every fact and phantom recorded inside the block with `horror_id`."""
        saved = self._horror
        if horror_id:
            self._horror = horror_id
            self.horrors.add(horror_id)
        try:
            yield
        finally:
            self._horror = saved

    def fact(self, channel: str, **values: Any) -> dict[str, Any]:
        if channel not in CHANNELS:
            raise KeyError(f"unknown channel {channel}")
        row = dict(values)
        if self._horror:
            row["horror"] = self._horror
        self.facts.setdefault(channel, []).append(row)
        return row

    def phantom(self, channel: str, why: str, **values: Any) -> None:
        """A fact that must NOT be recorded. The scorer reports every unkeyed engine fact as a
        phantom anyway; listing one here ties it to a horror and says why it is wrong."""
        row = {"channel": channel, **values, "why": why}
        if self._horror:
            row["horror"] = self._horror
        self.phantoms.append(row)

    def key_entry(self) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "app": self.app,
            "library": self.library,
            "language": self.language,
            "numbered": self.numbered,
            "lines": len(self.lines),
            "compile": self.compile,
        }
        if self.generated_from:
            entry["generated_from"] = self.generated_from
        for ch in CHANNELS:
            if self.facts.get(ch):
                entry[ch] = self.facts[ch]
        if self.phantoms:
            entry["phantoms"] = self.phantoms
        if self.horrors:
            entry["horrors"] = sorted(self.horrors)
        return entry
