"""BDLD -- Batch Badlands, the first Open World level estate (gitgalaxy#7065, #4891 JCL execution,
#4890 utilities). A nightly batch chain as a mid-sized shop runs it: a DFSORT step, a Db2 load program
run under IKJEFT01, a report step chosen by IF/THEN/ELSE, a restart job, a utility job (IDCAMS,
IEBGENER, ICETOOL, DFSORT) and a GDG job. The COBOL is deliberately small; the JCL is the subject.

Planted: H-0064 (COND, IF/THEN/ELSE/ENDIF), H-0065 (temporary datasets), H-0066 (DD concatenation),
H-0067 (utility control cards), H-0068 (IKJEFT01 running a Db2 program), H-0069 (PARM, RESTART),
H-0070 (GDG (0) / (+1) in one job), H-0071 (a cataloged procedure with symbolic parameters, run through
JCLLIB), H-0072 (further utility control cards: IDCAMS LISTCAT / ALTER / PRINT, IEBCOPY, DFSORT JOINKEYS /
OUTFIL), H-0073 (checkpoint restart: RD=R, SYSCKEOV, RESTART=(step,checkid) with SYSCHK), H-0074 (SYSOUT forms,
DD DUMMY, COND=EVEN / ONLY), H-0075 (overrides of a cataloged procedure's PARM, COND and DD), H-0083 (an INCLUDE
group), H-0084 (SET and DSN=NULLFILE), H-0085 (a DD added to a procedure step), H-0094 (job- and step-level
OUTPUT JCL statements referenced by sysout DDs), H-0095 (a COBOL program with a RERUN checkpoint clause)."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw, read, sql

H64, H65, H66, H67, H68, H69, H70, H71, H72, H73, H74, H75 = (
    "H-0064", "H-0065", "H-0066", "H-0067", "H-0068", "H-0069", "H-0070", "H-0071", "H-0072", "H-0073", "H-0074",
    "H-0075")
H83, H84, H85 = "H-0083", "H-0084", "H-0085"
H94, H95 = "H-0094", "H-0095"

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

BDLDCKP = {
    "member": "BDLDCKP",
    "era": 0,
    "era_evidence": "the RERUN clause of I-O-CONTROL is 1974/1985 COBOL; no later construct",
    "program_id": "BDLDCKP",
    "author": "BATCH OPERATIONS",
    "remarks": ["BDLDCKP - COUNT THE TRANSACTION EXTRACT.",
                "CHECKPOINT EVERY 1000 RECORDS (RERUN CLAUSE) TO THE SYSCKPT DD."],
    "selects": [{"name": "TRAN-FILE", "assign": "TRANIN", "status": "WS-TRAN-STATUS", "horror": H95,
                 "rerun": {"assign": "SYSCKPT", "every": 1000}}],
    "i_o_control": ["RERUN ON SYSCKPT EVERY 1000 RECORDS OF TRAN-FILE"],
    "special_names_horror": H95,
    "fds": [{"fd": "TRAN-FILE", "record": I(1, "TRAN-REC", copy=["BDLREC"])}],
    "ws": [
        I(1, "WS-TRAN-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-COUNT", "9(7)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT TRAN-FILE"),
             perform("8000-READ"),
             perform("1000-COUNT", until="WS-EOF"),
             raw("CLOSE TRAN-FILE", "DISPLAY 'BDLDCKP COUNTED ' WS-COUNT"),
             goback()),
        para("1000-COUNT",
             raw("ADD 1 TO WS-COUNT"),
             perform("8000-READ")),
        para("8000-READ",
             read("TRAN-FILE", at_end=[raw("SET WS-EOF TO TRUE")])),
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
                {"name": "SYSTSIN", "horror": H68, "inline": [
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
    {
        # a job that runs the cataloged procedure, overriding one symbolic, from a private library
        "name": "BDLDPRCJ",
        "title": "BDLD PROC RUN",
        "accounting": "(BDLD,0100)",
        "jcllib": ["PROD.BDLD.PROCLIB"],
        "horror": H71,
        "comments": ["RUN THE CATALOGED PROCEDURE BDLDPRC WITH RPT=MONTHLY"],
        "steps": [
            {"name": "MONTH", "proc": "BDLDPRC", "proc_parms": ["RPT=MONTHLY"]},
        ],
    },
    {
        # further utilities: IDCAMS LISTCAT / ALTER / PRINT, IEBCOPY, DFSORT JOINKEYS with OUTFIL
        "name": "BDLDUT2",
        "title": "BDLD UTILITIES 2",
        "accounting": "(BDLD,0100)",
        "steps": [
            {"name": "IDC010", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H72, "inline": [
                    ("LISTCAT", " LISTCAT ENTRIES(PROD.BDLD.XREF) ALL"),
                    ("ALTER", [" ALTER PROD.BDLD.XREF -", "       NEWNAME(PROD.BDLD.XREF2)"]),
                    ("PRINT", " PRINT INDATASET(PROD.BDLD.XREF2) COUNT(10)"),
                ]},
            ]},
            {"name": "CPY020", "pgm": "IEBCOPY", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("SYSUT1", "PROD.BDLD.LOADLIB"),
                _dd("SYSUT2", "PROD.BDLD.LOADBAK"),
                {"name": "SYSIN", "horror": H72, "inline": [
                    ("COPY", " COPY OUTDD=SYSUT2,INDD=SYSUT1"),
                    ("SELECT", " SELECT MEMBER=(BDLDRPT,BDLDDB2)"),
                ]},
            ]},
            {"name": "JNK030", "pgm": "SORT", "dds": [
                _dd("SORTJNF1", "PROD.BDLD.XREFIN"),
                _dd("SORTJNF2", "PROD.BDLD.XREFOUT"),
                {"name": "SYSOUT", "sysout": "*"},
                _dd("OUT1", "PROD.BDLD.JOINED", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=50)"]),
                _dd("OUT2", "PROD.BDLD.JOINREST", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=50)"]),
                {"name": "SYSIN", "horror": H72, "inline": [
                    ("JOINKEYS", " JOINKEYS F1=SORTJNF1,FIELDS=(1,10,A)"),
                    ("JOINKEYS", " JOINKEYS F2=SORTJNF2,FIELDS=(1,10,A)"),
                    ("REFORMAT", " REFORMAT FIELDS=(F1:1,40,F2:11,10)"),
                    ("SORT", " SORT FIELDS=COPY"),
                    ("OUTFIL", " OUTFIL FNAMES=OUT1,INCLUDE=(35,1,CH,EQ,C'A')"),
                    ("OUTFIL", " OUTFIL FNAMES=OUT2,SAVE"),
                ]},
            ]},
        ],
    },
    {
        # deferred checkpoint restart: the JOB names a checkid, SYSCHK precedes the first EXEC, RD=R on the step
        "name": "BDLDCHK",
        "title": "BDLD CHECKPOINT RUN",
        "accounting": "(BDLD,0100)",
        "job_extra": ["RESTART=(CHK020,C0000012)"],
        "restart": "CHK020",
        "restart_checkid": "C0000012",
        "comments": ["RESUBMITTED FROM CHECKPOINT C0000012 TAKEN IN CHK020"],
        "job_dds": [_dd("SYSCHK", "PROD.BDLD.CHKPT", ("OLD", "KEEP"), horror=H73)],
        "steps": [
            {"name": "CHK010", "pgm": "SORT", "horror": H73, "dds": [
                _dd("SORTIN", "PROD.BDLD.TRANS"),
                _dd("SORTOUT", "PROD.BDLD.CHKSORT", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "inline": [("SORT", " SORT FIELDS=(1,10,CH,A)")]},
            ]},
            {"name": "CHK020", "pgm": "SORT", "rd": "R", "horror": H73, "dds": [
                _dd("SORTIN", "PROD.BDLD.CHKSORT"),
                _dd("SORTOUT", "PROD.BDLD.CHKOUT", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                _dd("SYSCKEOV", "PROD.BDLD.CHKEOV", ("MOD", "KEEP")),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "inline": [("SORT", " SORT FIELDS=(1,10,CH,D)")]},
            ]},
        ],
    },
    {
        # SYSOUT forms and a DUMMY DD; COND=EVEN / ONLY run a step after an abend / only after one
        "name": "BDLDSYS",
        "title": "BDLD SYSOUT AND COND",
        "accounting": "(BDLD,0100)",
        "steps": [
            {"name": "SYS010", "pgm": "BDLDRPT", "horror": H74, "dds": [
                _dd("STEPLIB", LOADLIB),
                {"name": "RPTOUT", "sysout": "(A,,STD1)"},
                {"name": "AUDIT", "sysout": "Z", "extra": ["DEST=NYC01"]},
                {"name": "SYSUDUMP", "sysout": "*"},
                {"name": "TRACE", "dummy": True},
            ]},
            {"name": "SYS020", "pgm": "IEBGENER", "cond": "EVEN", "horror": H74, "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("SYSUT1", "PROD.BDLD.ERRMSG"),
                {"name": "SYSUT2", "sysout": "A"},
                {"name": "SYSIN", "dummy": True},
            ]},
            {"name": "SYS030", "pgm": "IEBGENER", "cond": "((4,LT,SYS010),ONLY)", "horror": H74, "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("SYSUT1", "PROD.BDLD.ERRMSG"),
                {"name": "SYSUT2", "sysout": "(B,,ERR1)"},
                {"name": "SYSIN", "dummy": True},
            ]},
        ],
    },
    {
        # a job step that overrides a cataloged procedure's PARM, COND and one DD by procedure step name
        "name": "BDLDOVR",
        "title": "BDLD PROC OVERRIDES",
        "accounting": "(BDLD,0100)",
        "jcllib": ["PROD.BDLD.PROCLIB"],
        "horror": H75,
        "steps": [
            {"name": "QTR", "proc": "BDLDPRC", "proc_parms": ["RPT=DAILY"],
             "parm_overrides": [("RPT020", "QUARTERLY")], "cond_overrides": [("RPT020", "(4,LT,SRT010)")],
             "dds": [{"name": "RPTOUT", "sysout": "B", "proc_step": "RPT020"}]},
        ],
    },
    {
        # an INCLUDE group (member BDLDDDS of the JCLLIB library) holds the step's output DDs
        "name": "BDLDINC",
        "title": "BDLD INCLUDE GROUP",
        "accounting": "(BDLD,0100)",
        "jcllib": ["PROD.BDLD.PROCLIB"],
        "horror": H83,
        "steps": [
            {"name": "INC010", "pgm": "IEBGENER", "include": ["BDLDDDS"], "dds": [
                _dd("SYSUT1", "PROD.BDLD.ERRMSG"),
                {"name": "SYSIN", "dummy": True},
            ]},
        ],
    },
    {
        # a SET statement assigns a symbolic parameter used in a DSN; DSN=NULLFILE is a dummy data set
        "name": "BDLDSET",
        "title": "BDLD SET NULLFILE",
        "accounting": "(BDLD,0100)",
        "steps": [
            {"name": "SET010", "pgm": "SORT", "set": [("HLQ", "PROD")], "horror": H84, "dds": [
                _dd("SORTIN", "&HLQ..BDLD.TRANS", horror=H84),
                _dd("SORTOUT", "PROD.BDLD.SETOUT", ("NEW", "CATLG", "DELETE"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(5,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SORTWK01", "dummy": True, "nullfile": True, "horror": H84},
                {"name": "SYSIN", "inline": [("SORT", " SORT FIELDS=(1,10,CH,A)")]},
            ]},
        ],
    },
    {
        # a DD added to a procedure step: its ddname is not on any procedure statement
        "name": "BDLDADD",
        "title": "BDLD ADDED DD",
        "accounting": "(BDLD,0100)",
        "jcllib": ["PROD.BDLD.PROCLIB"],
        "horror": H85,
        "steps": [
            {"name": "ADDQ", "proc": "BDLDPRC", "proc_parms": ["RPT=DAILY"],
             "dds": [{"name": "AUDIT", "sysout": "B", "proc_step": "RPT020", "added": True}]},
        ],
    },
    {
        # OUTPUT JCL statements: two at job level (before the first EXEC), one at step level; sysout DDs
        # reference them with *.name and *.stepname.name
        "name": "BDLDOUT",
        "title": "BDLD OUTPUT STATEMENTS",
        "accounting": "(BDLD,0100)",
        "horror": H94,
        "job_outputs": [
            {"name": "OUT1", "params": ["DEST=NYC01", "CLASS=A"]},
            {"name": "OUT2", "params": ["CONTROL=DOUBLE"]},
        ],
        "steps": [
            {"name": "OUT010", "pgm": "BDLDRPT", "outputs": [{"name": "LOCAL", "params": ["COPIES=2"]}], "dds": [
                _dd("STEPLIB", LOADLIB),
                {"name": "RPTOUT", "sysout": "A", "output_refs": ["*.OUT1", "*.OUT2", "*.LOCAL"]},
            ]},
            {"name": "OUT020", "pgm": "IEBGENER", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                _dd("SYSUT1", "PROD.BDLD.ERRMSG"),
                {"name": "SYSUT2", "sysout": "A", "output_refs": ["*.OUT010.LOCAL"]},
                {"name": "SYSIN", "dummy": True},
            ]},
        ],
    },
    {
        # a program with a RERUN clause: the step carries the checkpoint data set DD
        "name": "BDLDCKJ",
        "title": "BDLD CHECKPOINT PROGRAM",
        "accounting": "(BDLD,0100)",
        "horror": H95,
        "steps": [
            {"name": "CKP010", "pgm": "BDLDCKP", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("TRANIN", "PROD.BDLD.TRANS"),
                _dd("SYSCKPT", "PROD.BDLD.CHKPT", ("NEW", "KEEP"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))"]),
            ]},
        ],
    },
]

PROCS = [
    {
        # symbolic parameters (&HLQ, &RPT) in a DSN, in PARM; && (a temporary dataset) in the same member
        "name": "BDLDPRC",
        "symbolics": ["HLQ=PROD", "RPT=DAILY"],
        "horror": H71,
        "steps": [
            {"name": "SRT010", "pgm": "SORT", "dds": [
                _dd("SORTIN", "&HLQ..BDLD.TRANS"),
                _dd("SORTOUT", "&&WORK", ("NEW", "PASS"),
                    extra=["UNIT=SYSDA", "SPACE=(CYL,(1,1))", "DCB=(RECFM=FB,LRECL=40)"]),
                {"name": "SYSOUT", "sysout": "*"},
                {"name": "SYSIN", "inline": [("SORT", " SORT FIELDS=(1,10,CH,A)")]},
            ]},
            {"name": "RPT020", "pgm": "BDLDRPT", "parm": "&RPT", "dds": [
                _dd("STEPLIB", "&HLQ..BDLD.LOADLIB"),
                {"name": "RPTOUT", "sysout": "A"},
            ]},
        ],
    },
]

PROCS.append({
    # an INCLUDE group: bare DD statements imbedded where the INCLUDE statement stands (not a procedure)
    "name": "BDLDDDS",
    "include_group": True,
    "horror": H83,
    "steps": [],
    "job_dds": [{"name": "SYSPRINT", "sysout": "*"}, {"name": "SYSUT2", "sysout": "A"}],
})


APP = {
    "id": "BDLD",
    "era": 2,
    "era_evidence": "BDLDDB2 EXEC SQL and END-IF (COBOL-85); the JCL uses IF/THEN/ELSE/ENDIF",
    "title": "Batch Badlands (JCL execution flow and utilities)",
    "style": "multi-step batch jobs: COND, IF/THEN/ELSE, temp datasets, concatenation, utility control cards",
    "copybooks": COPYBOOKS,
    "dclgen": DCLGEN,
    "programs": [BDLDDB2, BDLDRPT, BDLDCKP],
    "jcl": JOBS,
    "procs": PROCS,
}
