"""LOAN -- loan servicing. A mixed library: an IDMS-DC program kept from a CA IDMS
conversion, and two batch programs whose PROGRAM-ID paragraphs lost their separator
period. None of the three compiles under GnuCOBOL as written (see each `compile_reason`).

Planted: H-0007 (IDMS-CONTROL SECTION / PROTOCOL, LNIDMS01), H-0008 (PROGRAM-ID without
its period, LNRATE and LNCALC)."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H7 = "H-0007"
H8 = "H-0008"

COPYBOOKS = [
    {
        "member": "LNREC",
        "header": [" LNREC    - LOAN MASTER RECORD (28 BYTES)"],
        "items": [
            I(5, "LN-ID", "X(12)"),
            I(5, "LN-PRINCIPAL", "S9(9)V99", "COMP-3"),
            I(5, "LN-RATE", "S9(3)V9(4)", "COMP-3"),
            I(5, "LN-TERM-MONTHS", "9(3)"),
            I(5, "LN-PAYMENT", "S9(7)V99", "COMP-3"),
        ],
    },
]

PERIOD_FIX = ("program-id-period", "the PROGRAM-ID line is rewritten to `PROGRAM-ID. <name>.` for the check; "
              "everything else compiles as written")

LNIDMS01 = {
    "member": "LNIDMS01",
    "program_id": "LNIDMS01",
    "numbered": True,
    "author": "LOAN SYSTEMS",
    "remarks": ["LNIDMS01 - LOAN LOOKUP, IDMS-DC. PRECOMPILED BY THE IDMS DMLC."],
    "compile": "ibm-only",
    "compile_reason": "CA IDMS DML: needs the IDMS DML precompiler (IDMS-CONTROL SECTION, SCHEMA SECTION, "
                      "BIND / OBTAIN / FINISH); GnuCOBOL has no IDMS precompiler",
    "idms": {"mode": "IDMS-DC", "subschema": "LOANSS01", "schema": "LOANSCHM", "horror": H7},
    "ws": [
        I(1, "WS-LOAN-KEY", "X(12)"),
        I(1, "WS-NOT-FOUND-CNT", "S9(5)", "COMP-3", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("BIND RUN-UNIT", "READY USAGE-MODE IS RETRIEVAL"),
             perform("1000-OBTAIN-LOAN"),
             raw("FINISH", "DC RETURN"),
             horror=H7),
        para("1000-OBTAIN-LOAN",
             raw("MOVE WS-LOAN-KEY TO LOAN-ID", "OBTAIN CALC LOAN"),
             if_("DB-REC-NOT-FOUND", [perform("9000-NOT-FOUND")]),
             horror=H7),
        para("9000-NOT-FOUND", raw("ADD 1 TO WS-NOT-FOUND-CNT"), horror=H7),
    ],
}

LNRATE = {
    "member": "LNRATE",
    "program_id": "LNRATE",
    "program_id_style": "padded-no-period",
    "program_id_horror": H8,
    # no AUTHOR paragraph: the next code line after the period-less PROGRAM-ID is the
    # ENVIRONMENT DIVISION header, as in #4307's CBLDB22 (an AUTHOR. line there hides the bug)
    "remarks": ["LNRATE - MONTHLY RATE RESET. CALLS LNCALC PER LOAN."],
    "compile": "ibm-only",
    "compile_reason": "PROGRAM-ID name with no separator period (Enterprise COBOL diagnoses and continues; "
                      "GnuCOBOL -std=ibm rejects it)",
    "compile_check": PERIOD_FIX,
    "selects": [{"name": "LOAN-FILE", "assign": "LOANIN", "status": "WS-LOAN-STATUS"}],
    "fds": [{"fd": "LOAN-FILE", "record": I(1, "LOAN-RECORD", copy=["LNREC"])}],
    "ws": [
        I(1, "WS-LOAN-STATUS", "X(2)", kids=[I(88, "WS-LOAN-EOF", value="'10'")]),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT LOAN-FILE"),
             perform("1000-NEXT-LOAN", until="WS-LOAN-EOF"),
             raw("CLOSE LOAN-FILE"),
             goback()),
        para("1000-NEXT-LOAN",
             raw("READ LOAN-FILE"),
             if_("NOT WS-LOAN-EOF", [call("LNCALC", using=["LOAN-RECORD"])])),
    ],
}

LNCALC = {
    "member": "LNCALC",
    "program_id": "LNCALC",
    "program_id_style": "keyword-no-period",
    "program_id_horror": H8,
    "author": "LOAN SYSTEMS",
    "remarks": ["LNCALC - LEVEL PAYMENT FOR ONE LOAN. CALLED BY LNRATE."],
    "compile": "ibm-only",
    "compile_reason": "PROGRAM-ID keyword with no separator period (Enterprise COBOL diagnoses and continues; "
                      "GnuCOBOL -std=ibm rejects it)",
    "compile_check": PERIOD_FIX,
    "ws": [I(1, "WS-MONTHLY-RATE", "S9(3)V9(8)", "COMP-3")],
    "linkage": [I(1, "LK-LOAN", copy=["LNREC"])],
    "using": ["LK-LOAN"],
    "units": [
        para("0000-MAIN",
             raw("COMPUTE WS-MONTHLY-RATE = LN-RATE / 1200",
                 "COMPUTE LN-PAYMENT ROUNDED = LN-PRINCIPAL * WS-MONTHLY-RATE"),
             goback()),
    ],
}

JOBS = [
    {
        "name": "LNBATCH",
        "title": "LOAN RATE RESET",
        "accounting": "(LOAN,0101)",
        "steps": [
            {"name": "RESET", "pgm": "LNRATE", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.LOAN.LOADLIB", "disp": ("SHR",)},
                {"name": "LOANIN", "dsn": "PROD.LOAN.MASTER", "disp": ("OLD",)},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "AUDIT", "proc": "AUDLOG", "cond": "(0,NE)"},
        ],
    },
]

APP = {
    "id": "LOAN",
    "title": "Loan servicing (IDMS, batch)",
    "style": "mixed: numbered IDMS-DC member, unnumbered batch; PROGRAM-ID periods missing",
    "copybooks": COPYBOOKS,
    "programs": [LNIDMS01, LNRATE, LNCALC],
    "jcl": JOBS,
}
