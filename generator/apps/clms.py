"""CLMS -- claims. A PL/I main program with internal procedures, calling a COBOL edit
routine.

Planted: H-0002 (#4301's PL/I shape, `ELSE RETURN;` in CHECK_CLAIM)."""

from ..data import I
from ..pli import pcall, pif, praw
from ..stmt import goback, if_, para, raw

H2 = "H-0002"

CLMPROC = {
    "member": "CLMPROC",
    "proc": "CLMPROC",
    "params": ["PARM"],
    "options": "MAIN",
    "comments": ["CLMPROC - CLAIMS VALIDATION. CALLS THE COBOL EDIT ROUTINE CLMEDIT."],
    "decls": [
        [(1, "PARM", "CHAR(100) VARYING")],
        [(1, "CLAIM", ""), (2, "CLM_ID", "CHAR(10)"), (2, "CLM_AMT", "FIXED DEC(9,2)"), (2, "CLM_STATUS", "CHAR(1)")],
        [("ENTRY", "CLMEDIT", "")],
    ],
    "stmts": [
        pcall("INIT_CLAIM"),
        pcall("CHECK_CLAIM"),
        pcall("CLMEDIT", "CLAIM", external=True),
        praw("RETURN;"),
    ],
    "internal": [
        {"name": "INIT_CLAIM", "stmts": [praw("CLM_ID = '';", "CLM_AMT = 0;")]},
        {"name": "CHECK_CLAIM", "horror": H2, "stmts": [
            pif("CLM_AMT > 0", [praw("CLM_STATUS = 'A';")], [praw("RETURN;")]),
            pcall("LOG_CLAIM"),
            pcall("WRITE_CLAIM"),
        ]},
        {"name": "LOG_CLAIM", "stmts": [praw("PUT SKIP LIST(CLM_ID);")]},
        {"name": "WRITE_CLAIM", "stmts": [praw("PUT SKIP LIST(CLM_STATUS);")]},
    ],
}

CLMEDIT = {
    "member": "CLMEDIT",
    "program_id": "CLMEDIT",
    "author": "CLAIMS",
    "remarks": ["CLMEDIT - EDIT ONE CLAIM. CALLED FROM PL/I (CLMPROC)."],
    "linkage": [I(1, "LK-CLAIM", kids=[I(5, "LK-CLM-ID", "X(10)"), I(5, "LK-CLM-AMT", "S9(7)V99", "COMP-3"),
                                       I(5, "LK-CLM-STATUS", "X")])],
    "using": ["LK-CLAIM"],
    "units": [
        para("0000-MAIN",
             if_("LK-CLM-AMT > 1000000", [raw("MOVE 'R' TO LK-CLM-STATUS")]),
             goback()),
    ],
}

APP = {
    "id": "CLMS",
    "title": "Claims (PL/I with a COBOL routine)",
    "style": "PL/I external procedure with internal procedures",
    "pli": [CLMPROC],
    "programs": [CLMEDIT],
}
