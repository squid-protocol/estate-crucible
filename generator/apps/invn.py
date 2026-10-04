"""INVN -- inventory maintenance, online. A CICS program over a VSAM file and a TS queue, a
Db2 access module, a large data-only item copybook, a job named after the program it runs.

Planted: H-0010 (#4330, a COPY holding its own 01 after a COPY-ed 01), H-0015 (D003),
H-0017 (D005), H-0018 (D006), H-0021 (D010), H-0024 (D022)."""

from ..data import C, I
from ..stmt import cics, comment_code, if_, para, perform, raw, sql

H10, H15, H17, H18, H21, H24 = "H-0010", "H-0015", "H-0017", "H-0018", "H-0021", "H-0024"


def _item_fields() -> list:
    """INVITEM: a data-only copybook of 60+ lines (an item master), no PROCEDURE code at all."""
    kids = [I(10, "INV-ITEM-ID", "X(12)"), I(10, "INV-DESC", "X(40)"), I(10, "INV-UOM", "X(4)")]
    for w in range(1, 7):
        kids.append(I(10, f"INV-WH{w}", kids=[
            I(15, f"INV-WH{w}-ID", "X(4)"),
            I(15, f"INV-WH{w}-ONHAND", "S9(7)", "COMP-3"),
            I(15, f"INV-WH{w}-ALLOC", "S9(7)", "COMP-3"),
            I(15, f"INV-WH{w}-REORDER", "S9(7)", "COMP-3"),
            I(15, f"INV-WH{w}-BIN", "X(8)"),
            I(15, f"INV-WH{w}-LAST-CNT", "9(8)"),
            I(15, f"INV-WH{w}-FLAG", "X", kids=[I(88, f"INV-WH{w}-ACTIVE", value="'A'")]),
        ]))
    kids += [I(10, "INV-COST", "S9(9)V9(4)", "COMP-3"), I(10, "INV-PRICE", "S9(9)V99", "COMP-3")]
    return [I(5, "INV-ITEM", kids=kids)]


COPYBOOKS = [
    {"member": "INVITEM", "header": [" INVITEM  - INVENTORY ITEM MASTER (DATA ONLY)"], "horror": H18,
     "items": _item_fields()},
    {"member": "INVCOMM", "header": [" INVCOMM  - INVENTORY COMMAREA (24 BYTES)"],
     "items": [I(5, "IC-ITEM-ID", "X(12)"), I(5, "IC-QTY", "S9(7)", "COMP-3"), I(5, "IC-RC", "S9(4)", "COMP"),
               I(5, "IC-FUNC", "X(6)")]},
    {"member": "INVMSG", "header": [" INVMSG   - INVENTORY MESSAGES (A RECORD OF ITS OWN)"],
     "items": [I(1, "INV-MSG-REC", kids=[I(5, "INV-MSG-CODE", "X(4)"), I(5, "INV-MSG-TEXT", "X(60)")])]},
]

DCLGEN = [
    {
        "member": "DCLINVT",
        "table": "PROD.INVENTORY",
        "library": "PROD.INVN.DCLGEN(DCLINVT)",
        "structure": "DCLINVENTORY",
        "horror": H15,
        "columns": [
            ("ITEM_ID", "CHAR", 12, None, False),
            ("ON_HAND", "DECIMAL", 9, 0, False),
            ("LAST_COUNT", "DATE", None, None, True),
        ],
    },
]

INVUPD = {
    "member": "INVUPD",
    "program_id": "INVUPD",
    "author": "INVENTORY",
    "remarks": ["INVUPD - ADJUST ON-HAND QUANTITY (TRANSACTION IUPD)."],
    "compile": "compiled-stubbed",
    "ws": [
        I(1, "WS-INV-AREA", copy=["INVCOMM"], horror=H10),
        C("INVMSG", horror=H10),
        I(1, "WS-ITEM-REC", copy=["INVITEM"], horror=H18),
        I(1, "WS-RESP", "S9(8)", "COMP"),
        I(1, "WS-TSQ-NAME", "X(8)", value="'INVAUDIT'"),
    ],
    "linkage": [I(1, "DFHCOMMAREA", copy=["INVCOMM"])],
    "units": [
        para("0000-MAIN",
             raw("MOVE DFHCOMMAREA TO WS-INV-AREA"),
             perform("1000-READ-ITEM"),
             if_("WS-RESP = 0", [perform("2000-ADJUST")]),
             perform("3000-AUDIT"),
             cics("RETURN")),
        para("1000-READ-ITEM",
             cics("READ FILE('INVFILE') INTO(WS-ITEM-REC)", "RIDFLD(IC-ITEM-ID OF WS-INV-AREA)",
                  "UPDATE RESP(WS-RESP)",
                  resource={"verb": "READ", "kind": "FILE", "name": "INVFILE", "record": "WS-ITEM-REC",
                            "access": "read"})),
        para("2000-ADJUST",
             raw("ADD IC-QTY OF WS-INV-AREA TO INV-WH1-ONHAND"),
             comment_code("CALL 'OLDINVAD' USING WS-INV-AREA", call="OLDINVAD", horror=H21),
             comment_code("PERFORM 2500-OLD-REORDER", horror=H21),
             cics("REWRITE FILE('INVFILE') FROM(WS-ITEM-REC)",
                  resource={"verb": "REWRITE", "kind": "FILE", "name": "INVFILE", "record": "WS-ITEM-REC",
                            "access": "update"}),
             cics("LINK PROGRAM('INVDB') COMMAREA(WS-INV-AREA)", verb="LINK", operand="INVDB", horror=H24)),
        para("3000-AUDIT",
             raw("MOVE IC-ITEM-ID OF WS-INV-AREA TO INV-MSG-CODE"),
             cics("WRITEQ TS QUEUE(WS-TSQ-NAME) FROM(INV-MSG-REC)",
                  resource={"verb": "WRITEQ", "kind": "QUEUE", "name": "INVAUDIT", "qualifier": "TS",
                            "record": "INV-MSG-REC", "access": "write"})),
    ],
}

INVDB = {
    "member": "INVDB",
    "program_id": "INVDB",
    "author": "INVENTORY",
    "remarks": ["INVDB - INVENTORY DB2 ACCESS. LINKED FROM INVUPD."],
    "compile": "compiled-stubbed",
    "ws": [
        {"sql_include": "SQLCA", "horror": H17},
        {"sql_include": "DCLINVT", "horror": H17},
        I(1, "WS-SQLCODE", "-9(9)"),
    ],
    "linkage": [I(1, "DFHCOMMAREA", copy=["INVCOMM"])],
    "units": [
        para("0000-MAIN",
             raw("MOVE IC-ITEM-ID TO ITEM-ID"),
             sql("UPDATE PROD.INVENTORY", "   SET ON_HAND = ON_HAND + :IC-QTY", " WHERE ITEM_ID = :ITEM-ID",
                 verb="UPDATE", table="PROD.INVENTORY", access="update"),
             if_("SQLCODE NOT = 0", [raw("MOVE SQLCODE TO WS-SQLCODE", "MOVE 8 TO IC-RC")]),
             cics("RETURN")),
    ],
}

CSD = [
    {
        "group": "INVGRP",
        "title": "INVENTORY",
        "defines": [
            ("PROGRAM", "INVUPD", {"LANGUAGE": "COBOL"}),
            ("PROGRAM", "INVDB", {"LANGUAGE": "COBOL"}),
            ("TRANSACTION", "IUPD", {"PROGRAM": "INVUPD"}),
            ("FILE", "INVFILE", {"DSNAME": "PROD.INVN.ITEMS"}),
        ],
    },
]

JOBS = [
    {
        # a job named after the program it runs: the JOB name INVDB is not a program (#3616)
        "name": "INVDB",
        "title": "INVENTORY DB2 RUNSTATS",
        "accounting": "(INVN,0100)",
        "steps": [
            {"name": "STATS", "pgm": "DSNUTILB", "parm": "DB2P,INVSTATS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "INVN",
    "title": "Inventory maintenance (CICS, VSAM, Db2)",
    "style": "unnumbered, CICS file and TS queue commands, a job named after a program",
    "copybooks": COPYBOOKS,
    "dclgen": DCLGEN,
    "programs": [INVUPD, INVDB],
    "csd": CSD,
    "jcl": JOBS,
}
