"""INVT -- inventory stock status, written in 1983. The estate's era-1 app: a card-deck batch
program (sequence numbers in cols 1-6, the deck name in 73-80, upper case throughout) built from
SECTIONs, period-terminated sentences, with no COBOL-85 construct. One program, one
record copybook, one job.

Planted: nothing (a skeleton for the era-1 horrors that follow, gitgalaxy#5118)."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw, section

COPYBOOKS = [
    {"member": "INVTREC", "numbered": True, "header": [" INVTREC  - INVENTORY STOCK RECORD (80 BYTES)"],
     "items": [
         I(5, "STK-PART-NO", "X(10)"),
         I(5, "STK-DESC", "X(30)"),
         I(5, "STK-ON-HAND", "S9(7)", "COMP-3"),
         I(5, "STK-REORDER-PT", "S9(7)", "COMP-3"),
         I(5, "STK-BIN", "X(6)"),
         I(5, "FILLER", "X(26)"),
     ]},
]

INVTBAT = {
    "member": "INVTBAT",
    "era": 1,
    "era_evidence": "SECTIONs and period-terminated sentences only; no END-IF, END-READ or inline PERFORM, so OS/VS COBOL (#5117 era 1)",
    "program_id": "INVTBAT",
    "numbered": True,
    "ident": "INVTBAT",
    "banner": [
        "*****************************************************************",
        "*   INVTBAT  -  STOCK STATUS REPORT, REORDER POINT CHECK        *",
        "*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 06/14/83     *",
        "*****************************************************************",
        "/",
    ],
    "author": "D KOWALCZYK",
    "installation": "MATERIALS CONTROL",
    "date_written": "06/14/83",
    "remarks": ["INVTBAT - LIST STOCK AT OR BELOW REORDER POINT."],
    "selects": [{"name": "STOCK-FILE", "assign": "STOCKIN", "status": "WS-STOCK-STATUS"},
                {"name": "LIST-FILE", "assign": "STKLIST", "status": "WS-LIST-STATUS"}],
    "fds": [{"fd": "STOCK-FILE", "record": I(1, "STOCK-IN", "X(80)")},
            {"fd": "LIST-FILE", "record": I(1, "LIST-LINE", "X(133)")}],
    "ws": [
        I(1, "WS-STOCK-STATUS", "X(2)"),
        I(1, "WS-LIST-STATUS", "X(2)"),
        I(1, "WS-EOF", "X", value="'N'"),
        I(1, "WS-LOW-COUNT", "9(5)", "COMP-3", value="0"),
        I(1, "WS-REC", copy=["INVTREC"]),
    ],
    "units": [
        section("0000-MAINLINE",
                raw("OPEN INPUT STOCK-FILE OUTPUT LIST-FILE"),
                perform("1000-PROCESS-STOCK", until="WS-EOF = 'Y'"),
                raw("CLOSE STOCK-FILE LIST-FILE"),
                goback()),
        section("1000-PROCESS-STOCK",
                perform("1100-READ-STOCK"),
                if_("WS-EOF NOT = 'Y'", [perform("1200-CHECK-REORDER")], end_if=False)),
        section("1100-READ-STOCK",
                raw("READ STOCK-FILE INTO WS-REC AT END MOVE 'Y' TO WS-EOF")),
        section("1200-CHECK-REORDER",
                if_("STK-ON-HAND NOT > STK-REORDER-PT",
                    [raw("ADD 1 TO WS-LOW-COUNT", "MOVE SPACES TO LIST-LINE", "MOVE STK-PART-NO TO LIST-LINE",
                         "WRITE LIST-LINE")], end_if=False)),
    ],
}

JOBS = [
    {
        "name": "INVTDLY",
        "title": "INVT STOCK STATUS",
        "accounting": "(INVT,0683)",
        "comments": ["NIGHTLY STOCK STATUS AND REORDER POINT LIST"],
        "steps": [
            {"name": "STEP010", "pgm": "INVTBAT", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.INVT.LOADLIB", "disp": ("SHR",)},
                {"name": "STOCKIN", "dsn": "PROD.INVT.STOCK", "disp": ("SHR",)},
                {"name": "STKLIST", "sysout": "A"},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "INVT",
    "era": 1,
    "era_evidence": "INVTBAT, the app's only program, has no construct later than OS/VS COBOL; a 1983 card-deck batch system",
    "title": "Inventory stock status (1983 batch deck)",
    "style": "1980s card deck: numbered cols 1-6, deck name in cols 73-80, upper case, SECTIONs, period-terminated IF",
    "copybooks": COPYBOOKS,
    "programs": [INVTBAT],
    "jcl": JOBS,
}
