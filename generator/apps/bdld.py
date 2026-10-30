"""BDLD -- Batch Badlands, the first Open World level estate (gitgalaxy#7065, #4891 JCL execution,
#4890 utilities). A nightly batch chain as a mid-sized shop runs it: a DFSORT step, a Db2 load program
run under IKJEFT01, a report step chosen by IF/THEN/ELSE, a restart job, a utility job (IDCAMS,
IEBGENER, ICETOOL, DFSORT) and a GDG job. The COBOL is deliberately small; the JCL is the subject.

Planted: H-0064 (COND, IF/THEN/ELSE/ENDIF), H-0065 (temporary datasets), H-0066 (DD concatenation),
H-0067 (utility control cards), H-0068 (IKJEFT01 running a Db2 program), H-0069 (PARM, RESTART),
H-0070 (GDG (0) / (+1) in one job)."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw, read, sql

H64, H65, H66, H67, H68, H69, H70 = ("H-0064", "H-0065", "H-0066", "H-0067", "H-0068", "H-0069", "H-0070")

COPYBOOKS = [
    {"member": "BDLREC", "header": [" BDLREC   - SORTED TRANSACTION EXTRACT (40 BYTES)"],
     "items": [I(5, "BDL-ACCT", "X(10)"), I(5, "BDL-NAME", "X(10)"), I(5, "BDL-AMT", "9(5)"),
               I(5, "BDL-PAD", "X(10)"), I(5, "BDL-STATUS", "X"), I(5, "FILLER", "X(4)")]},
]

DCLGEN = [
    {
        "member": "DCLBDLD",
        "table": "PROD.BDLD_SUMMARY",
        "library": "PROD.BDLD.DCLGEN(DCLBDLD)",
        "structure": "DCLBDLD-SUMMARY",
        "columns": [
            ("ACCT_ID", "CHAR", 10, None, False),
            ("TOTAL_AMT", "DECIMAL", 9, 0, False),
        ],
    },
]

BDLDDB2 = {
    "member": "BDLDDB2",
    "era": 2,
    "era_evidence": "EXEC SQL (Db2) is an era-2 tell in #5117; END-IF is COBOL-85",
    "program_id": "BDLDDB2",
    "author": "BATCH OPERATIONS",
    "remarks": ["BDLDDB2 - LOAD THE SORTED EXTRACT INTO BDLD_SUMMARY.",
                "RUNS UNDER IKJEFT01 (DSN RUN PROGRAM), STEP LOAD020."],
    "compile": "compiled-stubbed",
    "selects": [{"name": "SORTED-FILE", "assign": "SORTED", "status": "WS-SORTED-STATUS"}],
    "fds": [{"fd": "SORTED-FILE", "record": I(1, "SORTED-REC", copy=["BDLREC"])}],
    "ws": [
        {"sql_include": "SQLCA"},
        {"sql_include": "DCLBDLD"},
        I(1, "WS-SORTED-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-LOADED", "9(7)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT SORTED-FILE"),
             perform("8000-READ"),
             perform("1000-LOAD", until="WS-EOF"),
             raw("CLOSE SORTED-FILE", "DISPLAY 'BDLDDB2 LOADED ' WS-LOADED"),
             goback()),
        para("1000-LOAD",
             raw("MOVE BDL-ACCT TO ACCT-ID", "MOVE BDL-AMT TO TOTAL-AMT"),
             sql("INSERT INTO PROD.BDLD_SUMMARY (ACCT_ID, TOTAL_AMT)", "  VALUES (:ACCT-ID, :TOTAL-AMT)",
                 verb="INSERT", table="PROD.BDLD_SUMMARY", access="update"),
             if_("SQLCODE = 0", [raw("ADD 1 TO WS-LOADED")],
                 [raw("MOVE 8 TO RETURN-CODE", "SET WS-EOF TO TRUE")]),
             perform("8000-READ")),
        para("8000-READ",
             read("SORTED-FILE", at_end=[raw("SET WS-EOF TO TRUE")])),
    ],
}

BDLDRPT = {
    "member": "BDLDRPT",
    "era": 2,
    "era_evidence": "END-IF (COBOL-85) and a PARM received through LINKAGE; no later construct",
    "program_id": "BDLDRPT",
    "author": "BATCH OPERATIONS",
    "remarks": ["BDLDRPT - PRINT THE LOAD REPORT.",
                "THE EXEC PARM (A REPORT TYPE) ARRIVES IN LS-PARM."],
    "selects": [{"name": "RPT-FILE", "assign": "RPTOUT", "status": "WS-RPT-STATUS"}],
    "fds": [{"fd": "RPT-FILE", "record": I(1, "RPT-LINE", "X(80)")}],
    "ws": [I(1, "WS-RPT-STATUS", "X(2)")],
    "linkage": [I(1, "LS-PARM", kids=[I(5, "LS-PARM-LEN", "S9(4)", "COMP"), I(5, "LS-PARM-TEXT", "X(8)")])],
    "using": ["LS-PARM"],
    "units": [
        para("0000-MAIN",
             raw("OPEN OUTPUT RPT-FILE"),
             if_("LS-PARM-LEN > 0", [raw("MOVE SPACES TO RPT-LINE", "MOVE LS-PARM-TEXT TO RPT-LINE")],
                 [raw("MOVE 'REPORT DAILY' TO RPT-LINE")]),
             raw("WRITE RPT-LINE", "CLOSE RPT-FILE"),
             goback()),
    ],
}


def _dd(name, dsn=None, disp=("SHR",), **kw):
    return {"name": name, "dsn": dsn, "disp": disp, **kw}


LOADLIB = "PROD.BDLD.LOADLIB"
JOBS = [
    {
        # nightly chain: sort, Db2 load, then a report or an error copy by IF/THEN/ELSE
        "name": "BDLDNITE",
        "title": "BDLD NIGHTLY CHAIN",
        "accounting": "(BDLD,0100)",
        "comments": ["SORT THE EXTRACT, LOAD IT UNDER IKJEFT01, REPORT OR COPY THE ERRORS"],
        "steps": [
            {"name": "SORT010", "pgm": "SORT", "dds": [
                _dd("SORTIN", "PROD.BDLD.TRANS"),
                _dd("SORTOUT", "&&SORTED", ("NEW", "PASS"), horror=H65,
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "horror": H67, "inline": [
                    ("SORT", " SORT FIELDS=(1,10,CH,A)"),
                    ("INCLUDE", " INCLUDE COND=(35,1,CH,EQ,C'A')"),
                ]},
            ]},
            {"name": "LOAD020", "pgm": "IKJEFT01", "cond": "(4,LT,SORT010)", "horror": H64, "dds": [
                _dd("STEPLIB", "DSN.V13R1.SDSNLOAD", horror=H66),
                _dd("", LOADLIB, concat=True, horror=H66),
                _dd("SORTED", "&&SORTED", ("OLD", "DELETE"), horror=H65),
                {"name": "SYSTSPRT", "sysout": "*"},
                {"name": "SYSTSIN", "horror": H68, "inline": [
                    ("DSN", " DSN SYSTEM(DB2P)"),
                    ("RUN", " RUN PROGRAM(BDLDDB2) PLAN(BDLDPLN) LIB('PROD.BDLD.LOADLIB')"),
                    ("END", " END"),
                ]},
            ]},
            {"if": "LOAD020.RC = 0", "name": "IFOK", "horror": H64,
             "then": [{"name": "RPT030", "pgm": "BDLDRPT", "dds": [
                 _dd("STEPLIB", LOADLIB),
                 {"name": "RPTOUT", "sysout": "A"},
             ]}],
             "else": [{"name": "ERR040", "pgm": "IEBGENER", "dds": [
                 {"name": "SYSPRINT", "sysout": "*"},
                 _dd("SYSUT1", "PROD.BDLD.ERRMSG"),
                 {"name": "SYSUT2", "sysout": "A"},
                 {"name": "SYSIN", "dummy": True},
             ]}]},
        ],
    },
    {
        # the same chain resubmitted from LOAD020 after an abend in the first run
        "name": "BDLDRST",
        "title": "BDLD RESTART CHAIN",
        "accounting": "(BDLD,0100)",
        "job_extra": ["RESTART=LOAD020"],
        "restart": "LOAD020",
        "comments": ["RESUBMITTED WITH RESTART=LOAD020: SORT010 ALREADY RAN, ITS OUTPUT IS CATALOGED"],
        "steps": [
            {"name": "SORT010", "pgm": "SORT", "horror": H69, "dds": [
                _dd("SORTIN", "PROD.BDLD.TRANS"),
                _dd("SORTOUT", "PROD.BDLD.SORTED", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "inline": [("SORT", " SORT FIELDS=(1,10,CH,A)")]},
            ]},
            {"name": "LOAD020", "pgm": "IKJEFT01", "horror": H69, "dds": [
                _dd("STEPLIB", "DSN.V13R1.SDSNLOAD"),
                _dd("SORTED", "PROD.BDLD.SORTED"),
                {"name": "SYSTSPRT", "sysout": "*"},
                {"name": "SYSTSIN", "inline": [
                    ("DSN", " DSN SYSTEM(DB2P)"),
                    ("RUN", " RUN PROGRAM(BDLDDB2) PLAN(BDLDPLN) LIB('PROD.BDLD.LOADLIB')"),
                    ("END", " END"),
                ]},
            ]},
            {"name": "RPT030", "pgm": "BDLDRPT", "parm": "MONTHLY", "horror": H69, "dds": [
                _dd("STEPLIB", LOADLIB),
                {"name": "RPTOUT", "sysout": "A"},
            ]},
        ],
    },
    {
        # utilities: IDCAMS delete / define / repro, IEBGENER, ICETOOL, DFSORT reformatting
        "name": "BDLDUTIL",
        "title": "BDLD UTILITIES",
        "accounting": "(BDLD,0100)",
        "steps": [
            {"name": "IDC010", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("INDD", "PROD.BDLD.XREFIN"),
                {"name": "SYSIN", "horror": H67, "inline": [
                    ("DELETE", " DELETE PROD.BDLD.XREF CLUSTER PURGE"),
                    ("SET", " SET MAXCC=0"),
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.BDLD.XREF) -",
                                "        INDEXED KEYS(10 0) RECORDSIZE(40 40) -",
                                "        CYLINDERS(1 1))"]),
                    ("REPRO", " REPRO INFILE(INDD) OUTDATASET(PROD.BDLD.XREF)"),
                ]},
            ]},
            {"name": "GEN020", "pgm": "IEBGENER", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("SYSUT1", "PROD.BDLD.XREFIN"),
                _dd("SYSUT2", "PROD.BDLD.XREFBAK", ("NEW", "CATLG", "DELETE"), horror=H67,
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSIN", "dummy": True, "horror": H67},
            ]},
            {"name": "ICE030", "pgm": "ICETOOL", "dds": [
                {"name": "TOOLMSG", "sysout": "*"},
                {"name": "DFSMSG", "sysout": "*"},
                _dd("INDD", "PROD.BDLD.XREFIN"),
                _dd("OUTDD", "PROD.BDLD.XREFOUT", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "TOOLIN", "horror": H67, "inline": [
                    ("COPY", " COPY FROM(INDD) TO(OUTDD) USING(CTL1)")]},
                {"name": "CTL1CNTL", "horror": H67, "inline": [
                    ("OMIT", " OMIT COND=(35,1,CH,EQ,C'X')")]},
            ]},
            {"name": "SRT040", "pgm": "SORT", "dds": [
                _dd("SORTIN", "PROD.BDLD.XREFIN"),
                _dd("SORTOUT", "PROD.BDLD.XREFSUM", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "horror": H67, "inline": [
                    ("SORT", " SORT FIELDS=(1,10,CH,A)"),
                    ("INREC", " INREC FIELDS=(1,40)"),
                    ("SUM", " SUM FIELDS=(21,5,ZD)"),
                    ("OUTREC", " OUTREC FIELDS=(1,25,15X)"),
                ]},
            ]},
        ],
    },
    {
        # one job reads generation (0) and writes generation (+1) of the same group
        "name": "BDLDGDG",
        "title": "BDLD GDG ROLL",
        "accounting": "(BDLD,0100)",
        "steps": [
            {"name": "GEN010", "pgm": "SORT", "dds": [
                _dd("SORTIN", "PROD.BDLD.MASTER", gen="0", horror=H70),
                _dd("", "PROD.BDLD.DELTA", concat=True, horror=H66),
                _dd("SORTOUT", "PROD.BDLD.MASTER", ("NEW", "CATLG", "DELETE"), gen="+1", horror=H70,
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "horror": H67, "inline": [("SORT", " SORT FIELDS=(1,10,CH,A)")]},
            ]},
        ],
    },
]

APP = {
    "id": "BDLD",
    "era": 2,
    "era_evidence": "BDLDDB2 EXEC SQL and END-IF (COBOL-85); the JCL uses IF/THEN/ELSE/ENDIF",
    "title": "Batch Badlands (JCL execution flow and utilities)",
    "style": "multi-step batch jobs: COND, IF/THEN/ELSE, temp datasets, concatenation, utility control cards",
    "copybooks": COPYBOOKS,
    "dclgen": DCLGEN,
    "programs": [BDLDDB2, BDLDRPT],
    "jcl": JOBS,
}
