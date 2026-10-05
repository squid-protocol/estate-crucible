"""ORDR -- order entry (batch). The estate as a customer actually exports it: the edit routine
ORDVAL has been forked three times and nobody deleted the forks, the order record exists in
three libraries with three layouts, and a retired recovery paragraph is still in the driver.

* ORDVAL     the live edit routine (CALLed by ORDMAIN)
* ORDVALV2   a rewrite that never went live (own PROGRAM-ID, nothing calls it)
* ORDVOLD    the pre-1998 version, kept "just in case"; compiled with the OLD library first
* ORDV#OLD   a member copy of ORDVAL whose PROGRAM-ID still says ORDVAL
* ORDREC     ORDRCPY (current, 2 channel bytes), SHRCPY (enterprise standard), ORDROLD (retired)

Planted: H-0050 (same PROGRAM-ID in two members), H-0051 (dead forks), H-0052 (copybook
drift and per-program SYSLIB), H-0053 (COPY of a member no library holds, named like a
program), H-0054 (EXEC PGM of a program not in the estate), H-0055 (dead paragraph),
H-0056 (orphan copybook)."""

import copy

from ..data import I
from ..stmt import call, comment_code, goback, if_, para, perform, raw, read

H50, H51, H52, H53, H54, H55, H56 = "H-0050", "H-0051", "H-0052", "H-0053", "H-0054", "H-0055", "H-0056"

# the order record, current layout (ORDRCPY): 41 bytes
ORDREC_CURRENT = [
    I(5, "ORD-ID", "X(10)"), I(5, "ORD-CUST", "X(8)"), I(5, "ORD-ITEM", "X(12)"),
    I(5, "ORD-QTY", "S9(5)", "COMP-3"), I(5, "ORD-PRICE", "S9(7)V99", "COMP-3"),
    I(5, "ORD-STATUS", "X", kids=[I(88, "ORD-OPEN", value="'O'"), I(88, "ORD-REJECTED", value="'R'")]),
    I(5, "ORD-CHANNEL", "X(2)"),
]
# the retired layout (ORDROLD): zoned quantity, an 8-byte item code, no channel: 36 bytes
ORDREC_OLD = [
    I(5, "ORD-ID", "X(10)"), I(5, "ORD-CUST", "X(8)"), I(5, "ORD-ITEM", "X(8)"),
    I(5, "ORD-QTY", "9(5)"),
    I(5, "ORD-STATUS", "X", kids=[I(88, "ORD-OPEN", value="'O'"), I(88, "ORD-REJECTED", value="'R'")]),
    I(5, "FILLER", "X(4)"),
]

COPYBOOKS = [
    {"member": "ORDREC", "header": [" ORDREC   - ORDER RECORD, CURRENT LAYOUT (41 BYTES).",
                                    "            CHG0907 ADDED ORD-CHANNEL.",
                                    "            SEE ALSO SHRCPY(ORDREC), ORDROLD(ORDREC)."],
     "horror": H52, "items": ORDREC_CURRENT},
    {"member": "ORDPARM", "header": [" ORDPARM  - ORDVAL / ORDPRICE CALL PARAMETERS"],
     "items": [I(5, "PRM-FUNCTION", "X"), I(5, "PRM-RC", "S9(4)", "COMP"), I(5, "PRM-MSG", "X(30)")]},
    # nobody COPYs it any more: the history file went away with ORDHUPD in 2009
    {"member": "ORDHIST", "header": [" ORDHIST  - ORDER HISTORY RECORD (ORDHUPD, RETIRED 2009)"],
     "orphan": "no COPY in the estate names ORDHIST (its only user, ORDHUPD, is gone)", "orphan_horror": H56,
     "horror": H56,
     "items": [I(5, "HST-ORD-ID", "X(10)"), I(5, "HST-DATE", "9(8)"), I(5, "HST-ACTION", "X(2)")]},
]

OLD_COPYBOOKS = [
    {"member": "ORDREC", "header": [" ORDREC   - ORDER RECORD (1994 LAYOUT, 36 BYTES). DO NOT USE."],
     "horror": H52, "items": ORDREC_OLD},
]

# the live edit routine
ORDVAL = {
    "member": "ORDVAL",
    "program_id": "ORDVAL",
    "program_id_horror": H50,
    "author": "M OKAFOR",
    "date_written": "06/02/98",
    "remarks": ["ORDVAL - EDIT ONE ORDER. CALLED BY ORDMAIN."],
    "ws": [I(1, "WS-MAX-QTY", "S9(5)", "COMP-3", value="5000")],
    "linkage": [I(1, "LK-ORDER", copy=["ORDREC"], horror=H52), I(1, "LK-PARM", copy=["ORDPARM"])],
    "using": ["LK-ORDER", "LK-PARM"],
    "units": [
        para("0000-MAIN",
             raw("MOVE ZERO TO PRM-RC"),
             perform("1000-CHECK-QTY"),
             perform("2000-CHECK-CHANNEL"),
             goback()),
        para("1000-CHECK-QTY",
             if_("ORD-QTY > WS-MAX-QTY OR ORD-QTY NOT > ZERO",
                 [raw("SET ORD-REJECTED TO TRUE", "MOVE 8 TO PRM-RC")])),
        para("2000-CHECK-CHANNEL",
             if_("ORD-CHANNEL = SPACES", [raw("MOVE 'BT' TO ORD-CHANNEL")])),
    ],
}

# a rewrite that never went live: near-identical, one more check, its own PROGRAM-ID
ORDVALV2 = copy.deepcopy(ORDVAL)
ORDVALV2.update({
    "member": "ORDVALV2", "program_id": "ORDVALV2", "program_id_horror": H51, "date_written": "04/11/2016",
    "remarks": ["ORDVALV2 - ORDVAL REWRITE (ORDER-NG). NOT IN PRODUCTION."],
    "dead": "a rewrite never put into production: no CALL, job step or CSD entry names ORDVALV2",
    "dead_horror": H51,
})
ORDVALV2["units"] = ORDVALV2["units"] + [
    para("3000-CHECK-PRICE", if_("ORD-PRICE < ZERO", [raw("MOVE 12 TO PRM-RC")])),
]
ORDVALV2["units"][0] = para("0000-MAIN",
                            raw("MOVE ZERO TO PRM-RC"),
                            perform("1000-CHECK-QTY"),
                            perform("2000-CHECK-CHANNEL"),
                            perform("3000-CHECK-PRICE"),
                            goback())

# the pre-1998 version, compiled with the OLD library first: the 36-byte layout
ORDVOLD = {
    "member": "ORDVOLD",
    "program_id": "ORDVOLD",
    "program_id_horror": H51,
    "numbered": True,
    "author": "D PRZYBYL",
    "date_written": "09/30/94",
    "remarks": ["ORDVOLD - ORDER EDIT (1994). REPLACED BY ORDVAL 06/98.", "KEEP FOR AUDIT."],
    "syslib": ["ORDROLD", "ORDRCPY", "SHRCPY"],
    "dead": "replaced by ORDVAL in 1998: no CALL, job step or CSD entry names ORDVOLD",
    "dead_horror": H51,
    "ws": [I(1, "WS-MAX-QTY", "9(5)", value="1000")],
    "linkage": [I(1, "LK-ORDER", copy=["ORDREC"], horror=H52), I(1, "LK-PARM", copy=["ORDPARM"])],
    "using": ["LK-ORDER", "LK-PARM"],
    "units": [
        para("0000-MAIN",
             raw("MOVE ZERO TO PRM-RC"),
             perform("1000-CHECK-QTY"),
             goback()),
        para("1000-CHECK-QTY",
             if_("ORD-QTY > WS-MAX-QTY", [raw("SET ORD-REJECTED TO TRUE", "MOVE 8 TO PRM-RC")])),
    ],
}

# a member copy of ORDVAL taken before a change, never renamed inside
ORDV_OLD = copy.deepcopy(ORDVAL)
ORDV_OLD.update({
    "member": "ORDV#OLD", "stale_copy": True, "program_id_horror": H50,
    "remarks": ["ORDVAL - EDIT ONE ORDER. CALLED BY ORDMAIN.", "BACKUP TAKEN 2011-03-02 BEFORE CHG1188 (TK)"],
    "dead": "a member copy whose PROGRAM-ID is still ORDVAL: CALL 'ORDVAL' loads the program object ORDVAL, "
            "never this member",
    "dead_horror": H50,
})
ORDV_OLD["units"] = [ORDV_OLD["units"][0], ORDV_OLD["units"][1]]
ORDV_OLD["units"][0] = para("0000-MAIN", raw("MOVE ZERO TO PRM-RC"), perform("1000-CHECK-QTY"), goback())

ORDPRICE = {
    "member": "ORDPRICE",
    "program_id": "ORDPRICE",
    "author": "M OKAFOR",
    "remarks": ["ORDPRICE - PRICE ONE ORDER LINE. CALLED BY ORDMAIN."],
    "linkage": [I(1, "LK-ORDER", copy=["ORDREC"], horror=H52)],
    "using": ["LK-ORDER"],
    "units": [para("0000-MAIN", raw("COMPUTE ORD-PRICE = ORD-QTY * 1.25"), goback())],
}

ORDMAIN = {
    "member": "ORDMAIN",
    "program_id": "ORDMAIN",
    "numbered": True,
    "ident": "ORDMAIN",
    "author": "D PRZYBYL",
    "installation": "ORDER SYSTEMS",
    "date_written": "09/30/94",
    "remarks": ["ORDMAIN - NIGHTLY ORDER EDIT AND PRICING. JOB ORDNITE."],
    "compile": "incomplete",
    "compile_reason": "COPY ORDPRICE: the estate holds no copybook ORDPRICE (H-0053), so no compiler finds it",
    "compile_check": ("missing-copy", "a one-byte FILLER stands in for the missing COPY ORDPRICE"),
    "selects": [{"name": "ORDER-FILE", "assign": "ORDIN", "status": "WS-ORD-STATUS"}],
    "fds": [{"fd": "ORDER-FILE", "record": I(1, "ORD-IN-REC", "X(41)")}],
    "ws": [
        I(1, "WS-ORD-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-ORDER", copy=["ORDREC"], horror=H52),
        I(1, "WS-PARM", copy=["ORDPARM"]),
        # the pricing routine's own linkage copybook was never put in a library: COPY
        # ORDPRICE finds nothing, while the program ORDPRICE sits in ORDR's cobol/
        I(1, "WS-PRICE-PARM", copy=["ORDPRICE"], horror=H53),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT ORDER-FILE"),
             perform("1000-NEXT-ORDER", until="WS-EOF"),
             raw("CLOSE ORDER-FILE"),
             comment_code("PERFORM 9000-OLD-RECOVERY", perform="9000-OLD-RECOVERY", horror=H55),
             goback()),
        para("1000-NEXT-ORDER",
             read("ORDER-FILE", into="WS-ORDER", at_end=[raw("SET WS-EOF TO TRUE")],
                  not_at_end=[call("ORDVAL", using=["WS-ORDER", "WS-PARM"], horror=H50),
                              call("ORDPRICE", using=["WS-ORDER"])])),
        # retired with the 2003 restart redesign; its PERFORM is commented out above
        para("9000-OLD-RECOVERY",
             raw("DISPLAY 'ORDMAIN RESTART FROM CHECKPOINT'", "MOVE 'Y' TO WS-EOF-FLAG"),
             horror=H55,
             dead="no PERFORM or GO TO names it (its PERFORM is commented out) and 1000-NEXT-ORDER "
                  "before it is reached only by PERFORM; 0000-MAIN ends in GOBACK"),
    ],
}

JOBS = [
    {
        "name": "ORDNITE",
        "title": "ORDER NIGHTLY EDIT",
        "accounting": "(ORDR,0907)",
        "comments": ["NIGHTLY ORDER EDIT. STEP020 PURGE WAS DECOMMISSIONED 2012 (PROGRAM DELETED)."],
        "steps": [
            {"name": "STEP010", "pgm": "ORDMAIN", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.ORDR.LOADLIB", "disp": ("SHR",)},
                {"name": "ORDIN", "dsn": "PROD.ORDR.ORDERS", "disp": ("SHR",)},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "STEP020", "pgm": "ORDPURGE", "cond": "(4,LT)", "horror": H54, "dds": [
                {"name": "STEPLIB", "dsn": "PROD.ORDR.LOADLIB", "disp": ("SHR",)},
                {"name": "ORDIN", "dsn": "PROD.ORDR.ORDERS", "disp": ("OLD",)},
            ]},
        ],
    },
]

APP = {
    "id": "ORDR",
    "title": "Order entry (forked programs, drifting copybooks)",
    "style": "forks of one edit routine; one record in three libraries; per-program SYSLIB; dead code",
    "syslib": ["ORDRCPY", "ORDRDCL", "SHRCPY", "ORDROLD"],
    "copybooks": COPYBOOKS,
    "old_copybooks": OLD_COPYBOOKS,
    "programs": [ORDMAIN, ORDVAL, ORDVALV2, ORDVOLD, ORDV_OLD, ORDPRICE],
    "jcl": JOBS,
}
