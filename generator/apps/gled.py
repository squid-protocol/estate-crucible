"""GLED -- general ledger posting. The oldest code in the estate: numbered, identification
tags in cols 73-80, a PROGRAM-ID whose name sits on the next line, a spaced-out PROCEDURE
DIVISION header, paragraph headers in every legal form, END- and mixed-case paragraph
names, and an ASSIGN TO whose assignment-name is on the next line.

Planted: H-0013 (D001), H-0019 (D007), H-0020 (D008), H-0023 (D020), H-0026 (D036),
H-0027 (D037), H-0032 (D044)."""

from ..data import I
from ..stmt import goback, para, perform, raw, read

H13, H19, H20, H23, H26, H27, H32 = "H-0013", "H-0019", "H-0020", "H-0023", "H-0026", "H-0027", "H-0032"

GLPOST = {
    "member": "GLPOST",
    "program_id": "GLPOST",
    "program_id_style": "next-line",
    "program_id_horror": H19,
    "numbered": True,
    "author": "GENERAL LEDGER",
    "date_written": "02/01/84",
    "remarks": ["GLPOST - POST JOURNAL ENTRIES TO THE LEDGER."],
    "selects": [{"name": "JRNL-FILE", "assign": "JRNLIN", "status": "WS-JRNL-STATUS", "assign_split": "GL001000",
                 "horror": H32}],
    "fds": [{"fd": "JRNL-FILE", "record": I(1, "JRNL-REC", kids=[
        I(5, "JRNL-ACCT", "X(12)"), I(5, "JRNL-AMT", "S9(11)V99", "COMP-3"), I(5, "FILLER", "X(61)")])}],
    "ws": [
        I(1, "WS-JRNL-STATUS", "X(2)", kids=[I(88, "WS-JRNL-EOF", value="'10'")]),
        I(1, "WS-TOTAL", "S9(13)V99", "COMP-3", value="ZERO"),
    ],
    "procedure_header": "PROCEDURE        DIVISION",
    "procedure_header_horror": H23,
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT JRNL-FILE"),
             perform("1000-INIT"),
             perform("2000-POST", until="WS-JRNL-EOF"),
             perform("END-IPROC1"),
             perform("End-Program"),
             goback(),
             tag="GL000100", horror=H13),
        para("1000-INIT", raw("MOVE ZERO TO WS-TOTAL"), perform("1100-OPEN-MSG"), header="inline", horror=H23),
        para("1100-OPEN-MSG", raw("DISPLAY 'GLPOST START'"), header="period-next-line", horror=H20),
        para("2000-POST",
             read("JRNL-FILE", at_end=[raw("SET WS-JRNL-EOF TO TRUE")],
                  not_at_end=[raw("ADD JRNL-AMT TO WS-TOTAL")]),
             tag="GL002000", horror=H13),
        para("END-IPROC1", raw("CLOSE JRNL-FILE"), horror=H26),
        para("End-Program", raw("DISPLAY 'GLPOST TOTAL ' WS-TOTAL"), horror=H27),
    ],
}

JOBS = [
    {
        "name": "GLNIGHT",
        "title": "LEDGER POSTING",
        "accounting": "(GLED,0001)",
        "steps": [
            {"name": "POST", "pgm": "GLPOST", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.GLED.LOADLIB", "disp": ("SHR",)},
                {"name": "JRNLIN", "dsn": "PROD.GLED.JOURNAL", "gen": "0", "disp": ("SHR",)},
            ]},
        ],
    },
]

APP = {
    "id": "GLED",
    "title": "General ledger (batch, oldest code)",
    "style": "numbered, cols 73-80 identification, every paragraph-header form",
    "programs": [GLPOST],
    "jcl": JOBS,
}
