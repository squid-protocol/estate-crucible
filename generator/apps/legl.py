"""LEGL -- general-ledger reconciliation, written in 1983 and maintained ever since. Card-era
members: a comment banner ahead of IDENTIFICATION DIVISION, a change log that quotes the
code it replaced, page ejects, sequence numbers in cols 1-6 and the deck name in 73-80 of
every line.

Planted: H-0055 (9900-TAPE-RESTART), H-0057."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw

H55, H57 = "H-0055", "H-0057"

BANNER = [
    "*****************************************************************",
    "*                                                               *",
    "*   GLRCON  -  GENERAL LEDGER RECONCILIATION                    *",
    "*   SYSTEM  :  GL / FINANCIAL REPORTING                         *",
    "*   AUTHOR  :  H. VANDERMEER        DATE: 03/11/83              *",
    "*                                                               *",
    "*   INPUT   :  GLMAST (VSAM KSDS), GLTRAN (QSAM)                *",
    "*   OUTPUT  :  RECON REPORT (SYSOUT=A)                          *",
    "*   CALLS   :  NONE. (WAS: CALL 'DTCONV' USING WS-DATE)         *",
    "*                                                               *",
    "*****************************************************************",
    "/",
]

HISTORY = [
    "CHANGE LOG",
    "DATE     BY   REQ#     DESCRIPTION",
    "-------- ---- -------- ------------------------------------",
    "04/02/86 HV   R86-014  REMOVED COPY OLDDATE, USE GLDATE",
    "11/19/91 PK   R91-233  PERFORM 9000-ABEND ON BAD STATUS",
    "06/07/99 TS   Y2K-0412 CALL 'DTCONV' REPLACED BY WINDOWING",
    "09/12/03 TS   R03-118  TAPE RESTART RETIRED (SEE 9900-...)",
    "          -->  PERFORM 9900-TAPE-RESTART NO LONGER CODED",
]

PHANTOMS = [
    {"channel": "call_sites", "verb": "CALL", "operand": "DTCONV", "horror": H57,
     "why": "DTCONV appears only in comment lines (the banner and the change log)"},
    {"channel": "edges", "kind": "call", "from": None, "target": "DTCONV", "horror": H57,
     "why": "DTCONV appears only in comment lines"},
    {"channel": "copies", "member": "OLDDATE", "horror": H57, "why": "COPY OLDDATE is change-log prose"},
    {"channel": "edges", "kind": "perform", "from": None, "target": "9000-ABEND", "horror": H57,
     "why": "PERFORM 9000-ABEND is change-log prose"},
    {"channel": "edges", "kind": "perform", "from": None, "target": "9900-TAPE-RESTART", "horror": H57,
     "why": "PERFORM 9900-TAPE-RESTART is change-log prose"},
]

GLRCON = {
    "member": "GLRCON",
    "program_id": "GLRCON",
    "numbered": True,
    "ident": "GLRCON",
    "banner": BANNER,
    "banner_horror": H57,
    "program_id_horror": H57,
    "author": "H VANDERMEER",
    "installation": "CORPORATE ACCOUNTING",
    "date_written": "03/11/83",
    "remarks": HISTORY,
    "phantoms": PHANTOMS,
    "ws": [
        I(1, "WS-GL-DATE", "9(8)", value="ZERO", horror=H57),
        I(1, "WS-DIFF", "S9(11)V99", "COMP-3", value="ZERO", horror=H57),
        I(1, "WS-STATUS", "X(2)", value="'00'", horror=H57),
    ],
    "units": [
        para("0000-MAINLINE",
             perform("1000-COMPARE"),
             if_("WS-STATUS NOT = '00'", [perform("9000-ABEND")]),
             goback(), horror=H57),
        para("1000-COMPARE",
             raw("COMPUTE WS-DIFF = WS-DIFF + 0"), horror=H57),
        para("9000-ABEND",
             raw("DISPLAY 'GLRCON ABEND, STATUS ' WS-STATUS", "MOVE 16 TO RETURN-CODE"),
             goback(), horror=H57),
        para("9900-TAPE-RESTART",
             raw("DISPLAY 'GLRCON RESTART FROM TAPE CHECKPOINT'"),
             horror=H55,
             dead="no PERFORM or GO TO names it (only the change log does); 9000-ABEND before it ends in GOBACK"),
    ],
}

GLRSUM = {
    "member": "GLRSUM",
    "program_id": "GLRSUM",
    "numbered": True,
    "ident": "GLRSUM",
    "banner": [
        "*****************************************************************",
        "*   GLRSUM  -  GL SUMMARY BY COST CENTRE                        *",
        "*   NOTE: DO NOT COPY GLWORK HERE - SEE GLRCON 1000-COMPARE      *",
        "*****************************************************************",
        "/",
    ],
    "banner_horror": H57,
    "phantoms": [
        {"channel": "copies", "member": "GLWORK", "horror": H57, "why": "COPY GLWORK appears only in the banner"},
        {"channel": "edges", "kind": "perform", "from": None, "target": "1000-COMPARE", "horror": H57,
         "why": "1000-COMPARE is named in the banner; GLRSUM has no such paragraph"},
    ],
    "author": "P KOWALCZYK",
    "date_written": "11/19/91",
    "ws": [I(1, "WS-CC-TOTAL", "S9(11)V99", "COMP-3", value="ZERO")],
    "units": [
        para("0000-MAINLINE", perform("1000-SUM"), goback()),
        para("1000-SUM", raw("ADD 1 TO WS-CC-TOTAL")),
    ],
}

APP = {
    "id": "LEGL",
    "title": "General-ledger reconciliation (card-era members)",
    "style": "comment banners before IDENTIFICATION DIVISION, change logs quoting old code, / page "
             "ejects, cols 1-6 sequence numbers and the deck name in cols 73-80",
    "programs": [GLRCON, GLRSUM],
}
