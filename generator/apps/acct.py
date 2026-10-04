"""ACCT -- nightly account posting. An old batch shop: every member carries ISPF sequence
numbers in cols 1-6, some paragraphs carry change tags in cols 73-80.

Planted: H-0001 (split operands, ACCTUPD), H-0003 (main-line code, ACCTPOST),
H-0004 (same-line COPY, ACCTRPT), H-0006 (inline PERFORM forms, ACCTRPT),
H-0002 shape 3 (EXIT PERFORM mid-paragraph, ACCTRPT 2500-SCAN-HISTORY)."""

from ..data import I
from ..stmt import (
    call,
    exit_para,
    exit_perform,
    goback,
    goto,
    if_,
    para,
    perform,
    perform_inline,
    raw,
    read,
)

COPYBOOKS = [
    {
        "member": "ACCTREC",
        "numbered": True,
        "header": [" ACCTREC  - ACCOUNT MASTER RECORD (152 BYTES)"],
        "items": [
            I(5, "ACCT-ID", "X(10)"),
            I(5, "ACCT-STATUS", "X", kids=[I(88, "ACCT-ACTIVE", value="'A'"), I(88, "ACCT-CLOSED", value="'C'")]),
            I(5, "ACCT-NAME", "X(30)"),
            I(5, "ACCT-BALANCE", "S9(11)V99", "COMP-3"),
            I(5, "ACCT-OPEN-DATE", "9(8)"),
            I(5, "ACCT-OPEN-DATE-R", redefines="ACCT-OPEN-DATE",
              kids=[I(10, "ACCT-OPEN-YYYY", "9(4)"), I(10, "ACCT-OPEN-MM", "99"), I(10, "ACCT-OPEN-DD", "99")]),
            I(5, "ACCT-TRAN-CNT", "S9(7)", "COMP"),
            I(5, "ACCT-HIST", occurs=12, kids=[I(10, "ACCT-HIST-AMT", "S9(9)V99", "COMP-3")]),
            I(5, "FILLER", "X(20)"),
        ],
    },
    {
        "member": "TRANREC",
        "numbered": True,
        "header": [" TRANREC  - DAILY TRANSACTION RECORD (51 BYTES)"],
        "items": [
            I(5, "TRAN-ACCT-ID", "X(10)"),
            I(5, "TRAN-TYPE", "X", kids=[I(88, "TRAN-DEBIT", value="'D'"), I(88, "TRAN-CREDIT", value="'C'")]),
            I(5, "TRAN-AMOUNT", "S9(9)V99", "COMP-3"),
            I(5, "TRAN-DATE", "9(8)"),
            I(5, "TRAN-REF", "X(16)"),
            I(5, "FILLER", "X(10)"),
        ],
    },
    {
        "member": "UPDCTL",
        "numbered": True,
        "header": [" UPDCTL   - ACCOUNT UPDATE CONTROL AREA"],
        "items": [
            I(5, "UPD-FLAG", "X", kids=[I(88, "UPD-REQUESTED", value="'Y'")]),
            I(5, "UPD-COUNT", "S9(5)", "COMP-3"),
            I(5, "UPD-LAST-ACCT", "X(10)"),
        ],
    },
    {
        "member": "RPTHDR",
        "numbered": True,
        "header": [" RPTHDR   - REPORT HEADING LINE"],
        "items": [
            I(5, "RPT-CC", "X", value="'1'"),
            I(5, "RPT-TITLE", "X(40)", value="'DAILY ACCOUNT ACTIVITY'"),
            I(5, "RPT-PAGE-LIT", "X(6)", value="'PAGE '"),
            I(5, "RPT-PAGE", "ZZZ9"),
        ],
    },
    {
        "member": "RPTTOT",
        "numbered": True,
        "header": [" RPTTOT   - REPORT MONEY TOTALS"],
        "items": [
            I(5, "TOT-DEBITS", "S9(11)V99", "COMP-3"),
            I(5, "TOT-CREDITS", "S9(11)V99", "COMP-3"),
        ],
    },
    {
        "member": "RPTCNT",
        "numbered": True,
        "header": [" RPTCNT   - REPORT RECORD COUNTS"],
        "items": [
            I(5, "CNT-READ", "S9(7)", "COMP"),
            I(5, "CNT-WRITTEN", "S9(7)", "COMP"),
        ],
    },
]

ACCTPOST = {
    "member": "ACCTPOST",
    "program_id": "ACCTPOST",
    "numbered": True,
    "author": "R HALVORSEN",
    "installation": "CENTRAL DATA PROCESSING",
    "date_written": "03/14/89",
    "remarks": [
        "ACCTPOST - APPLY THE DAY'S TRANSACTIONS TO THE ACCOUNT MASTER.",
        "BATCH. RUN BY JOB ACCTDLY THROUGH PROC ACCTPRC.",
        "THE MAIN LINE STARTS RIGHT AFTER THE PROCEDURE DIVISION",
        "HEADER (NO PARAGRAPH NAME), AS THIS SHOP'S OLDER PROGRAMS DO.",
    ],
    "configuration": True,
    "selects": [
        {"name": "TRAN-FILE", "assign": "TRANIN", "status": "WS-TRAN-STATUS"},
        {"name": "ACCT-OUT", "assign": "ACCTOUT", "status": "WS-ACCT-STATUS"},
    ],
    "fds": [
        {"fd": "TRAN-FILE", "record": I(1, "TRAN-RECORD", copy=["TRANREC"])},
        {"fd": "ACCT-OUT", "record": I(1, "ACCT-OUT-REC", copy=["ACCTREC"])},
    ],
    "ws": [
        I(1, "WS-FLAGS", kids=[
            I(5, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
            I(5, "WS-TRAN-STATUS", "X(2)"),
            I(5, "WS-ACCT-STATUS", "X(2)"),
        ]),
        I(1, "WS-COUNTERS", kids=[
            I(5, "WS-READ-CNT", "S9(7)", "COMP-3", value="ZERO"),
            I(5, "WS-POST-CNT", "S9(7)", "COMP-3", value="ZERO"),
            I(5, "WS-REJ-CNT", "S9(7)", "COMP-3", value="ZERO"),
        ]),
        I(1, "WS-DATE-AREA", copy=["DATEWS"]),
        I(1, "WS-ACCOUNT", copy=["ACCTREC"]),
        I(1, "WS-DATE-PGM", "X(8)", value="'DATEUTIL'"),
    ],
    "mainline_horror": "H-0003",
    "mainline": [
        raw("OPEN INPUT  TRAN-FILE", "     OUTPUT ACCT-OUT"),
        perform("1000-INITIALIZE", thru="1000-EXIT"),
        perform("2000-PROCESS-TRAN", thru="2000-EXIT", until="WS-EOF"),
        perform("9000-TERMINATE"),
        goback(),
    ],
    "units": [
        para("1000-INITIALIZE",
             raw("INITIALIZE WS-COUNTERS WS-ACCOUNT"),
             call("DATEUTIL", ident="WS-DATE-PGM", using=["WS-DATE-AREA"]),
             perform("8000-READ-TRAN")),
        para("1000-EXIT", exit_para()),
        para("2000-PROCESS-TRAN",
             if_("TRAN-DEBIT", [perform("2100-POST-DEBIT")], [perform("2200-POST-CREDIT")]),
             raw("ADD 1 TO WS-POST-CNT"),
             perform("8000-READ-TRAN")),
        para("2000-EXIT", exit_para()),
        para("2100-POST-DEBIT",
             raw("SUBTRACT TRAN-AMOUNT FROM ACCT-BALANCE OF WS-ACCOUNT"),
             if_("ACCT-BALANCE OF WS-ACCOUNT < ZERO", [perform("2900-REJECT")])),
        para("2200-POST-CREDIT",
             raw("ADD TRAN-AMOUNT TO ACCT-BALANCE OF WS-ACCOUNT")),
        para("2900-REJECT",
             raw("ADD 1 TO WS-REJ-CNT", "DISPLAY 'ACCTPOST REJECT ' TRAN-ACCT-ID"), tag="CHG0233"),
        para("8000-READ-TRAN",
             read("TRAN-FILE", at_end=[raw("SET WS-EOF TO TRUE")], not_at_end=[raw("ADD 1 TO WS-READ-CNT")])),
        para("9000-TERMINATE",
             raw("WRITE ACCT-OUT-REC FROM WS-ACCOUNT",
                 "CLOSE TRAN-FILE ACCT-OUT",
                 "DISPLAY 'ACCTPOST READ    ' WS-READ-CNT",
                 "DISPLAY 'ACCTPOST POSTED  ' WS-POST-CNT",
                 "DISPLAY 'ACCTPOST REJECTS ' WS-REJ-CNT"), tag="CHG0412"),
    ],
}

H1 = "H-0001"
ACCTUPD = {
    "member": "ACCTUPD",
    "program_id": "ACCTUPD",
    "numbered": True,
    "author": "R HALVORSEN",
    "date_written": "11/02/91",
    "remarks": [
        "ACCTUPD - APPLY MAINTENANCE REQUESTS TO THE UPDATE CONTROL AREA.",
        "SEVERAL STATEMENTS HAVE THEIR OPERAND ON THE NEXT LINE (THE",
        "VERB ALONE ON ITS LINE), AS AN OLD LINE-EDITOR HABIT LEFT THEM.",
    ],
    "ws": [
        I(1, "WS-UPD-CONTROL", copy=["UPDCTL"], copy_style="split", horror=H1),
        I(1, "WS-AUDIT-PGM", "X(8)", value="'ACCTAUD'"),
        I(1, "WS-MSG", "X(40)", horror="H-0009"),
    ],
    "units": [
        para("0000-MAIN",
             perform("1000-OPEN"),
             perform("2000-APPLY-UPDATES", split=True, horror=H1),
             if_("UPD-COUNT > 9999", [goto("9999-ABEND", split=True, horror=H1)]),
             call("ACCTLOG", using=["WS-MSG"], split=True, horror=H1),
             call("ACCTAUD", ident="WS-AUDIT-PGM", using=["WS-UPD-CONTROL"], split=True, horror=H1),
             perform("9000-CLOSE"),
             goback()),
        para("1000-OPEN", raw("MOVE 'ACCTUPD STARTED' TO WS-MSG", "DISPLAY WS-MSG")),
        para("2000-APPLY-UPDATES", raw("ADD 1 TO UPD-COUNT", "MOVE 'Y' TO UPD-FLAG")),
        para("9000-CLOSE", raw("MOVE 'ACCTUPD ENDED' TO WS-MSG", "DISPLAY WS-MSG")),
        para("9999-ABEND", raw("DISPLAY 'ACCTUPD UPDATE LIMIT EXCEEDED'", "MOVE 16 TO RETURN-CODE"), goback()),
    ],
}

ACCTAUD = {
    "member": "ACCTAUD",
    "program_id": "ACCTAUD",
    "numbered": True,
    "author": "R HALVORSEN",
    "remarks": ["ACCTAUD - AUDIT TRAIL FOR UPDATE CONTROL. CALLED DYNAMICALLY."],
    "linkage": [I(1, "LK-UPD-CONTROL", copy=["UPDCTL"])],
    "using": ["LK-UPD-CONTROL"],
    "units": [
        para("0000-MAIN", raw("DISPLAY 'ACCTAUD ' UPD-LAST-ACCT ' ' UPD-COUNT"), goback()),
    ],
}

H4 = "H-0004"
H6 = "H-0006"
ACCTRPT = {
    "member": "ACCTRPT",
    "program_id": "ACCTRPT",
    "numbered": True,
    "author": "M OKONKWO",
    "date_written": "06/30/97",
    "remarks": [
        "ACCTRPT - DAILY ACCOUNT ACTIVITY REPORT.",
        "HEADING AND TOTAL AREAS ARE COPIED ON THE SAME LINE AS THEIR 01.",
    ],
    "selects": [{"name": "RPT-FILE", "assign": "RPTOUT", "status": "WS-RPT-STATUS"}],
    "fds": [{"fd": "RPT-FILE", "record": I(1, "RPT-LINE", "X(133)")}],
    "ws": [
        I(1, "WS-RPT-HEAD", copy=["RPTHDR"], copy_style="same-line", horror=H4),
        I(1, "WS-RPT-TOTALS", copy=["RPTTOT", "RPTCNT"], copy_style="same-line", horror=H4),
        I(1, "WS-RPT-STATUS", "X(2)"),
        I(1, "WS-I", "9(4)", "COMP", value="0"),
        I(1, "WS-J", "9(4)", "COMP", value="0"),
        I(1, "WS-N", "9(4)", "COMP", value="3"),
        I(1, "WS-HIST-TABLE", kids=[I(5, "WS-HIST-AMT", "S9(9)V99", "COMP-3", occurs=12)]),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN OUTPUT RPT-FILE"),
             perform("1000-HEADINGS"),
             perform("2000-DETAIL", test="AFTER", until="WS-I > 12"),
             perform("2500-SCAN-HISTORY"),
             perform("3000-TOTALS"),
             raw("CLOSE RPT-FILE"),
             goback()),
        para("1000-HEADINGS",
             perform_inline("TEST AFTER VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 2",
                            [raw("WRITE RPT-LINE FROM WS-RPT-HEAD")], horror=H6),
             raw("MOVE 0 TO WS-I")),
        para("2000-DETAIL",
             perform_inline("WS-N TIMES", [raw("ADD 1 TO CNT-READ")], horror=H6),
             perform_inline("3 TIMES", [raw("ADD 1 TO CNT-WRITTEN")], horror=H6),
             perform_inline("TEST BEFORE UNTIL WS-J > 9", [raw("ADD 1 TO WS-J")], horror=H6),
             raw("ADD 1 TO WS-I")),
        para("2500-SCAN-HISTORY",
             perform_inline("VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 12", [
                 if_("WS-HIST-AMT (WS-J) = ZERO", [exit_perform(horror=H6)]),
                 raw("ADD WS-HIST-AMT (WS-J) TO TOT-DEBITS"),
             ]),
             perform("2600-HISTORY-DONE"),
             horror="H-0002"),
        para("2600-HISTORY-DONE", raw("MOVE 0 TO WS-J")),
        para("3000-TOTALS",
             perform("3100-FORMAT-TOTAL", times="2"),
             raw("WRITE RPT-LINE FROM WS-RPT-TOTALS")),
        para("3100-FORMAT-TOTAL", raw("ADD TOT-DEBITS TO TOT-CREDITS")),
    ],
}

JOBS = [
    {
        "name": "ACCTDLY",
        "title": "ACCT DAILY POSTING",
        "accounting": "(ACCT,0412)",
        "comments": ["NIGHTLY ACCOUNT POSTING, MAINTENANCE AND REPORT"],
        "steps": [
            {"name": "STEP010", "pgm": "IEFBR14", "dds": [
                {"name": "POSTWORK", "dsn": "PROD.ACCT.POSTWORK", "disp": ("MOD", "DELETE", "DELETE"),
                 "extra": ["SPACE=(TRK,(1,1))", "UNIT=SYSDA"]},
            ]},
            {"name": "STEP020", "proc": "ACCTPRC"},
            {"name": "STEP030", "pgm": "ACCTUPD", "cond": "(4,LT)", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.ACCT.LOADLIB", "disp": ("SHR",)},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "STEP040", "pgm": "ACCTRPT", "cond": "(4,LT)", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.ACCT.LOADLIB", "disp": ("SHR",)},
                {"name": "RPTOUT", "sysout": "A"},
            ]},
            {"name": "STEP050", "proc": "AUDLOG"},
        ],
    },
]

PROCS = [
    {
        "name": "ACCTPRC",
        "steps": [
            {"name": "POST", "pgm": "ACCTPOST", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.ACCT.LOADLIB", "disp": ("SHR",)},
                {"name": "TRANIN", "dsn": "PROD.ACCT.TRANS", "gen": "0", "disp": ("SHR",)},
                {"name": "ACCTOUT", "dsn": "PROD.ACCT.MASTER", "gen": "+1", "disp": ("NEW", "CATLG", "DELETE"),
                 "extra": ["SPACE=(CYL,(5,5),RLSE)", "DCB=(RECFM=FB,LRECL=152)"], "horror": "H-0011"},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "ACCT",
    "title": "Account posting (batch)",
    "style": "numbered fixed format, change tags, THRU-range paragraphs, main-line code",
    "copybooks": COPYBOOKS,
    "programs": [ACCTPOST, ACCTUPD, ACCTAUD, ACCTRPT],
    "jcl": JOBS,
    "procs": PROCS,
}
