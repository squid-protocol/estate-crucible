"""BILL -- monthly billing. Numbered members with ISPF blank lines between paragraphs (the
sequence number kept on the empty line), change markers in the sequence area, a record
copybook with REDEFINES and nested groups, SIGN SEPARATE amounts, unnamed FILLER entries.

Planted: H-0009 (#4329, USAGE read into the PROCEDURE DIVISION), H-0011 (#4331, GDG
relative generations), H-0012 (#4332, numbered blank lines), H-0014 (D002), H-0025
(D024), H-0030 (D042)."""

from ..data import C, I
from ..stmt import goback, if_, para, perform, raw, read

H9, H11, H12, H14, H25, H30 = "H-0009", "H-0011", "H-0012", "H-0014", "H-0025", "H-0030"

COPYBOOKS = [
    {
        "member": "BILREC",
        "numbered": True,
        "header": [" BILREC   - BILLING RECORD (110 BYTES)"],
        "horror": H14,
        "items": [
            I(1, "BIL-RECORD", kids=[
                I(5, "BIL-KEY", kids=[
                    I(10, "BIL-ACCT", "X(10)"),
                    I(10, "BIL-CYCLE", "9(6)"),
                ]),
                I(5, "BIL-KEY-R", redefines="BIL-KEY", kids=[I(10, "BIL-KEY-ALL", "X(16)")]),
                I(5, "BIL-CUST", kids=[
                    I(10, "BIL-NAME", "X(30)", seq="BL0412"),
                    I(10, "BIL-ADDR", kids=[
                        I(15, "BIL-STREET", "X(30)"),
                        I(15, "BIL-ZIP", "X(10)", seq="BL0412"),
                    ]),
                ]),
                I(5, "BIL-AMOUNT", "S9(9)V99", "COMP-3"),
                I(5, "BIL-TAX", "S9(7)V99", "COMP-3"),
                I(5, "FILLER", "X(4)"),
            ]),
            I(1, "BIL-TRAILER-COUNT", "9(7)"),
        ],
    },
]

BILLCALC = {
    "member": "BILLCALC",
    "program_id": "BILLCALC",
    "numbered": True,
    "author": "BILLING",
    "date_written": "09/12/88",
    "remarks": [
        "BILLCALC - COMPUTE THE MONTHLY BILL FOR EACH ACCOUNT.",
        "PARAGRAPHS ARE SEPARATED BY EMPTY NUMBERED LINES.",
    ],
    "configuration": True,
    "selects": [{"name": "BIL-FILE", "assign": "BILLIN", "status": "WS-BIL-STATUS"}],
    "fds": [{"fd": "BIL-FILE", "record": C("BILREC")}],
    "ws": [
        I(1, "WS-BIL-STATUS", "X(2)", kids=[I(88, "WS-BIL-EOF", value="'10'")]),
        I(1, "WS-PRINT-LINE", horror=H30, kids=[
            I(5, None, "X(6)", value="'BILL: '", horror=H30),
            I(5, "WS-PRT-ACCT", "X(10)"),
            I(5, None, "X(2)", value="SPACES", horror=H30),
            I(5, "WS-PRT-AMOUNT", "-Z(8)9.99"),
        ]),
        I(1, "WS-SIGNED", horror=H25, kids=[
            I(5, "WS-ADJUST", "S9(7)V99", sign="LEADING SEPARATE", horror=H25),
            I(5, "WS-CREDIT", "S9(5)", sign="TRAILING SEPARATE", horror=H25),
        ]),
        I(1, "WS-RATE", "9V9(4)", value="0.0725"),
        I(1, "WS-MODE", "X(8)"),
        # the last entry: no USAGE of its own; the PROCEDURE DIVISION's literal 'BINARY' must
        # not become one (#4329)
        I(1, "WS-LEN", "9(4)", horror=H9),
    ],
    "units": [
        para("0000-MAIN",
             raw("MOVE 'BINARY' TO WS-MODE", "MOVE 12 TO WS-LEN", "OPEN INPUT BIL-FILE"),
             perform("1000-NEXT-BILL", until="WS-BIL-EOF"),
             raw("CLOSE BIL-FILE"),
             goback(),
             horror=H12, blank_after=True),
        para("1000-NEXT-BILL",
             read("BIL-FILE", at_end=[raw("SET WS-BIL-EOF TO TRUE")], not_at_end=[perform("2000-COMPUTE")]),
             horror=H12, blank_after=True),
        para("2000-COMPUTE",
             raw("COMPUTE BIL-TAX = BIL-AMOUNT * WS-RATE"),
             if_("BIL-TAX < ZERO", [perform("2100-ADJUST")]),
             perform("3000-PRINT"),
             horror=H12, blank_after=True),
        para("2100-ADJUST",
             raw("MOVE BIL-TAX TO WS-ADJUST"),
             horror=H12, blank_after=True),
        para("3000-PRINT",
             raw("MOVE BIL-ACCT TO WS-PRT-ACCT", "MOVE BIL-AMOUNT TO WS-PRT-AMOUNT", "DISPLAY WS-PRINT-LINE"),
             horror=H12, blank_after=True),
    ],
}

JOBS = [
    {
        "name": "BILLMTH",
        "title": "MONTHLY BILLING",
        "accounting": "(BILL,0900)",
        "steps": [
            {"name": "CALC", "pgm": "BILLCALC", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.BILL.LOADLIB", "disp": ("SHR",)},
                {"name": "BILLIN", "dsn": "PROD.BILL.MASTER", "gen": "0", "disp": ("SHR",), "horror": H11},
                {"name": "BILLPRV", "dsn": "PROD.BILL.MASTER", "gen": "-1", "disp": ("SHR",), "horror": H11},
                {"name": "BILLOUT", "dsn": "PROD.BILL.MASTER", "gen": "+1", "disp": ("NEW", "CATLG", "DELETE"),
                 "extra": ["SPACE=(CYL,(10,5),RLSE)"], "horror": H11},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "BILL",
    "title": "Monthly billing (batch)",
    "style": "numbered, blank numbered lines, change markers in cols 1-6, GDG generations",
    "copybooks": COPYBOOKS,
    "programs": [BILLCALC],
    "jcl": JOBS,
}
