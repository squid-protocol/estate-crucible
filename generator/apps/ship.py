"""SHIP -- shipment inquiry (CICS). An online app whose export is incomplete: the menu program
it XCTLs to and the audit program it LINKs to were never exported, its CSD group still
defines a retired transaction, the rate routine's linkage copybook is missing, and the
pre-CICS-TS version of the inquiry is still in the library.

Planted: H-0051 (SHPINQO, a dead fork), H-0052 (COPY ORDREC takes SHRCPY's), H-0053 (COPY
SHPRATE, a program name), H-0054 (XCTL / LINK / CSD PROGRAM / TRANSACTION of missing
programs)."""

import copy

from ..data import C, I
from ..stmt import cics, goback, if_, para, perform, raw

H51, H52, H53, H54 = "H-0051", "H-0052", "H-0053", "H-0054"

COPYBOOKS = [
    {"member": "SHPCOMM", "header": [" SHPCOMM  - SHIPMENT INQUIRY COMMAREA (60 BYTES)"],
     "items": [I(5, "CA-ORD-ID", "X(10)"), I(5, "CA-RC", "S9(4)", "COMP"), I(5, "CA-CARRIER", "X(8)"),
               I(5, "CA-MSG", "X(40)")]},
]

SHPINQ = {
    "member": "SHPINQ",
    "program_id": "SHPINQ",
    "author": "LOGISTICS IT",
    "remarks": ["SHPINQ - SHIPMENT INQUIRY (TRANSACTION SHPI)."],
    "compile": "incomplete",
    "compile_reason": "COPY SHPRATE: the estate holds no copybook SHPRATE (H-0053), so no compiler finds it",
    "compile_check": ("missing-copy", "EXEC blocks stubbed; a one-byte FILLER stands in for the missing COPY SHPRATE"),
    "ws": [
        I(1, "WS-COMMAREA", copy=["SHPCOMM"]),
        I(1, "WS-ORDER", copy=["ORDREC"], horror=H52),
        # SHPRATE's parameter list: the copybook was never exported; SHPRATE.cbl is the program
        I(1, "WS-RATE-PARM", copy=["SHPRATE"], horror=H53),
        C("DFHAID"),
        I(1, "WS-RESP", "S9(8)", "COMP"),
    ],
    "linkage": [I(1, "DFHCOMMAREA", "X(60)")],
    "units": [
        para("0000-MAIN",
             if_("EIBCALEN = 0",
                 [cics("SEND TEXT FROM(WS-COMMAREA) ERASE"),
                  cics("RETURN TRANSID('SHPI')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="SHPI")]),
             raw("MOVE DFHCOMMAREA TO WS-COMMAREA"),
             if_("EIBAID = DFHPF3",
                 [cics("XCTL PROGRAM('SHPMENU')", verb="XCTL", operand="SHPMENU", horror=H54)]),
             perform("1000-RATE"),
             perform("2000-AUDIT"),
             cics("RETURN TRANSID('SHPI')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="SHPI")),
        para("1000-RATE",
             raw("MOVE CA-ORD-ID TO ORD-ID"),
             cics("LINK PROGRAM('SHPRATE')", "COMMAREA(WS-COMMAREA)", verb="LINK", operand="SHPRATE")),
        para("2000-AUDIT",
             cics("LINK PROGRAM('SHPAUDT')", "COMMAREA(WS-COMMAREA)", verb="LINK", operand="SHPAUDT",
                  horror=H54)),
    ],
}

# the version before the 2014 CICS TS migration: no audit LINK; nothing defines or calls it
SHPINQO = copy.deepcopy(SHPINQ)
SHPINQO.update({
    "member": "SHPINQO", "program_id": "SHPINQO", "program_id_horror": H51,
    "remarks": ["SHPINQ - SHIPMENT INQUIRY (TRANSACTION SHPI).", "PRE-CICS-TS VERSION, KEPT 2014."],
    "dead": "the pre-migration SHPINQ: no transaction, LINK or XCTL names SHPINQO", "dead_horror": H51,
})
SHPINQO["units"] = SHPINQO["units"][:2]
SHPINQO["units"][0] = para(
    "0000-MAIN",
    if_("EIBCALEN = 0",
        [cics("SEND TEXT FROM(WS-COMMAREA) ERASE"),
         cics("RETURN TRANSID('SHPI')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="SHPI")]),
    raw("MOVE DFHCOMMAREA TO WS-COMMAREA"),
    if_("EIBAID = DFHPF3", [cics("XCTL PROGRAM('SHPMENU')", verb="XCTL", operand="SHPMENU", horror=H54)]),
    perform("1000-RATE"),
    cics("RETURN TRANSID('SHPI')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="SHPI"))

SHPRATE = {
    "member": "SHPRATE",
    "program_id": "SHPRATE",
    "author": "LOGISTICS IT",
    "remarks": ["SHPRATE - CARRIER RATE LOOKUP (LINKED FROM SHPINQ)."],
    "compile": "compiled-stubbed",
    "linkage": [I(1, "DFHCOMMAREA", copy=["SHPCOMM"])],
    "units": [para("0000-MAIN",
                   if_("CA-CARRIER = SPACES", [raw("MOVE 'GROUND' TO CA-CARRIER")]),
                   cics("RETURN"))],
}

CSD = [
    {
        "group": "SHPGRP",
        "title": "SHIPMENT INQUIRY",
        "defines": [
            ("PROGRAM", "SHPINQ", {"LANGUAGE": "COBOL"}),
            ("PROGRAM", "SHPRATE", {"LANGUAGE": "COBOL"}),
            ("PROGRAM", "SHPMENU", {"LANGUAGE": "COBOL", "_horror": H54}),
            ("PROGRAM", "SHPLEGA", {"LANGUAGE": "COBOL", "_horror": H54}),
            ("TRANSACTION", "SHPI", {"PROGRAM": "SHPINQ"}),
            ("TRANSACTION", "SHPL", {"PROGRAM": "SHPLEGA", "_horror": H54}),
        ],
    },
]

APP = {
    "id": "SHIP",
    "title": "Shipment inquiry (CICS, an incomplete export)",
    "style": "CICS; XCTL / LINK / CSD entries for programs the export lacks; a dead fork",
    "copybooks": COPYBOOKS,
    "programs": [SHPINQ, SHPINQO, SHPRATE],
    "csd": CSD,
}
