"""SHIP -- shipment inquiry (CICS). An online app whose export is incomplete: the menu program
it XCTLs to and the audit program it LINKs to were never exported, its CSD group still
defines a retired transaction, the rate routine's linkage copybook is missing, and the
pre-CICS-TS version of the inquiry is still in the library.

Planted: H-0051 (SHPINQO, a dead fork), H-0052 (COPY ORDREC takes SHRCPY's), H-0053 (COPY
SHPRATE, a program name), H-0054 (XCTL / LINK / CSD PROGRAM / TRANSACTION of missing
programs), H-0063 (SHPTBL, CICS resource macro tables in HLASM)."""

import copy

from ..data import C, I
from ..stmt import cics, goback, if_, para, perform, raw

H51, H52, H53, H54, H63 = "H-0051", "H-0052", "H-0053", "H-0054", "H-0063"

COPYBOOKS = [
    {"member": "SHPCOMM", "header": [" SHPCOMM  - SHIPMENT INQUIRY COMMAREA (60 BYTES)"],
     "items": [I(5, "CA-ORD-ID", "X(10)"), I(5, "CA-RC", "S9(4)", "COMP"), I(5, "CA-CARRIER", "X(8)"),
               I(5, "CA-MSG", "X(40)")]},
]

SHPINQ = {
    "member": "SHPINQ",
    "era": 2,
    "era_evidence": "END-IF is COBOL-85 and the EXEC CICS XCTL / LINK commands are CICS/ESA-level DPL-capable command syntax (#5117 era 2; no RESP or HANDLE in the member)",
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
    "era": 2,
    "era_evidence": "END-IF scope terminator is COBOL-85 (VS COBOL II / COBOL 85; #5117 era 2)",
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
        "era": 2,
        "era_evidence": "CSD DEFINE PROGRAM / TRANSACTION is RDO (CICS/MVS 2.x, #5117 era 2)",
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

MACRO_TABLES = [
    {
        "member": "SHPTBL",
        "csect": "SHPTBL",
        "numbered": True,
        "horror": H63,
        "era": 0,
        "era_evidence": "HLASM CICS resource definition macro tables (DFHFCT, DFHPCT, DFHPPT, etc.) define resources prior to RDO (era 0)",
        "comments": [
            "SHPTBL - PRE-RDO CICS RESOURCE MACRO TABLES FOR SHIPMENT INQUIRY",
            "KEPT FOR BDAM FILE SHPDAM, EXTRAPARTITION QUEUE SHPA AND SEQUENTIAL",
            "TERMINAL S002 THAT CANNOT MOVE TO RDO CSD.",
        ],
        "statements": [
            # DFHFCT: alternative macro format with per-line remarks + a remark-only continuation line starting at col 17
            {"op": "DFHFCT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "label": "SHP_DAM_FILE_01",
                "op": "DFHFCT",
                "lines": [
                    ("TYPE=FILE,", "DEFINE SHIPMENT DAM FILE"),
                    ("FILE=SHPDAM,", "8-CHARACTER FILE IDENTIFIER"),
                    ("ACCMETH=BDAM,", "BASIC DIRECT ACCESS METHOD"),
                    ("DSNAME=PROD.SHIP.DAM,", "MVS DATASET NAME"),
                    ("RECFORM=(FIXED,BLOCKED),", "FIXED BLOCKED RECORDS"),
                    ("KEYLEN=10,LRECL=120", "KEY AND RECORD LENGTH"),
                    (" DSNAME=FAKE.REMARK.DSN", "COL 16 BLANK -> REMARK LINE"),
                ],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "FILE",
                        "name": "SHPDAM",
                        "group": "DFHFCT01",
                        "dsname": "PROD.SHIP.DAM",
                        "record_format": "F",
                    }
                ],
            },
            {
                "op": "DFHFCT",
                "lines": [
                    ("TYPE=DATASET,DATASET=SHPLOG,DSNAME=PROD.SHIP.LOG,", ""),
                    ("RECFORM=(VARIABLE,BLOCKED)", ""),
                ],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "FILE",
                        "name": "SHPLOG",
                        "group": "DFHFCT01",
                        "dsname": "PROD.SHIP.LOG",
                        "record_format": "V",
                    }
                ],
            },
            # DFHPCT: sequence symbol in name field, quoted operand with spaces, routes SHPM -> SHPINQ
            {"op": "DFHPCT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "label": ".PCT01",
                "op": "DFHPCT",
                "lines": [
                    ("TYPE=ENTRY,TRANSID=SHPM,DESC='SHIPMENT MACRO INQ',", ""),
                    ("PROGRAM=SHPINQ,TWASIZE=64,TRNPRTY=100,DTB=(YES,WAIT)", ""),
                ],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "TRANSACTION",
                        "name": "SHPM",
                        "group": "DFHPCT01",
                        "program": "SHPINQ",
                    },
                    {"channel": "transactions", "transid": "SHPM", "program": "SHPINQ", "group": "DFHPCT01"},
                ],
            },
            # DFHPPT: PROGRAM= with USAGE=MAP -> MAPSET; PARTSET= -> PARTITIONSET
            {"op": "DFHPPT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "op": "DFHPPT",
                "operands": ["TYPE=ENTRY", "PROGRAM=SHPMAP1", "USAGE=MAP"],
                "facts": [{"channel": "csd_resources", "type": "MAPSET", "name": "SHPMAP1", "group": "DFHPPT01"}],
            },
            {
                "op": "DFHPPT",
                "operands": ["TYPE=ENTRY", "PARTSET=SHPPSET"],
                "facts": [
                    {"channel": "csd_resources", "type": "PARTITIONSET", "name": "SHPPSET", "group": "DFHPPT01"}
                ],
            },
            # DFHDCT: SDSCI folded into EXTRA (with DESTID truncated to 4 chars: SHPAUD -> SHPA), plus INTRA
            {"op": "DFHDCT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "op": "DFHDCT",
                "operands": ["TYPE=SDSCI", "DSCNAME=SHPOUT", "RECFORM=VARBLKA", "BLKSIZE=1360", "RECSIZE=136"],
                "phantoms": [
                    {
                        "channel": "csd_resources",
                        "type": "TDQUEUE",
                        "name": "SHPOUT",
                        "why": "DFHDCT TYPE=SDSCI is the dataset control block for an EXTRA queue, not a queue itself",
                    }
                ],
            },
            {
                "op": "DFHDCT",
                "operands": ["TYPE=EXTRA", "DESTID=SHPAUD", "DSCNAME=SHPOUT"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "TDQUEUE",
                        "name": "SHPA",
                        "group": "DFHDCT01",
                        "record_format": "VARIABLE",
                    }
                ],
            },
            {
                "op": "DFHDCT",
                "operands": ["TYPE=INTRA", "DESTID=SHPI", "TRANSID=SHPM", "TRIGLEV=1"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "TDQUEUE",
                        "name": "SHPI",
                        "group": "DFHDCT01",
                        "transid": "SHPM",
                        "trigger_level": 1,
                    }
                ],
            },
            # DFHTST: refused empty DATAID=() vs retained 4-char prefix DATAID=SHPT,SHPA
            {"op": "DFHTST", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {"op": "DFHTST", "operands": ["TYPE=SHARED", "DATAID=()"]},
            {
                "op": "DFHTST",
                "operands": ["TYPE=RECOVERY", "DATAID=(SHPT,SHPA)"],
                "facts": [
                    {"channel": "csd_resources", "type": "TSMODEL", "name": "SHPT", "group": "DFHTST01"},
                    {"channel": "csd_resources", "type": "TSMODEL", "name": "SHPA", "group": "DFHTST01"},
                ],
            },
            # DFHSRT: refused RECOVER=NO vs retained system abends
            {"op": "DFHSRT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "op": "DFHSRT",
                "operands": ["TYPE=SYSTEM", "ABCODE=(0C1,0C4,0C7)", "RECOVER=YES"],
                "facts": [
                    {"channel": "csd_resources", "type": "SRT", "name": "S0C1", "group": "DFHSRT01"},
                    {"channel": "csd_resources", "type": "SRT", "name": "S0C4", "group": "DFHSRT01"},
                    {"channel": "csd_resources", "type": "SRT", "name": "S0C7", "group": "DFHSRT01"},
                ],
            },
            {"op": "DFHSRT", "operands": ["TYPE=USER", "ABCODE=(A001)", "RECOVER=NO"]},
            # DFHJCT: JFILEID=SYSTEM -> SYSTEM, JFILEID=02 -> 02
            {"op": "DFHJCT", "operands": ["TYPE=INITIAL", "SUFFIX=01"]},
            {
                "op": "DFHJCT",
                "operands": ["TYPE=ENTRY", "JFILEID=SYSTEM", "DSNAME=PROD.CICS.SYSTEM.LOG"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "JOURNAL",
                        "name": "SYSTEM",
                        "group": "DFHJCT01",
                        "dsname": "PROD.CICS.SYSTEM.LOG",
                    }
                ],
            },
            {
                "op": "DFHJCT",
                "operands": ["TYPE=ENTRY", "JFILEID=02", "DSNAME=PROD.CICS.USER.LOG02"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "JOURNAL",
                        "name": "02",
                        "group": "DFHJCT01",
                        "dsname": "PROD.CICS.USER.LOG02",
                    }
                ],
            },
            # DFHTCT: refused TYPE=SDSCI/LINE vs retained SYSTEM/REGION/TERMINAL/GPENTRY
            {"op": "DFHTCT", "operands": ["TYPE=INITIAL", "SUFFIX=01", "ACCMETH=(VTAM,NONVTAM)"]},
            {
                "op": "DFHTCT",
                "operands": ["TYPE=SYSTEM", "SYSIDNT=TOR1"],
                "facts": [{"channel": "csd_resources", "type": "CONNECTION", "name": "TOR1", "group": "DFHTCT01"}],
            },
            {"op": "DFHTCT", "operands": ["TYPE=REGION", "SYSIDNT=AOR1"]},
            {"op": "DFHTCT", "operands": ["TYPE=SDSCI", "DSCNAME=LINE01"]},
            {"op": "DFHTCT", "operands": ["TYPE=LINE", "ACCMETH=BTAM", "DSCNAME=LINE01"]},
            {
                "op": "DFHTCT",
                "operands": ["TYPE=TERMINAL", "TRMIDNT=T001", "TRMTYPE=3270"],
                "facts": [{"channel": "csd_resources", "type": "TERMINAL", "name": "T001", "group": "DFHTCT01"}],
            },
            {
                "op": "DFHTCT",
                "operands": ["TYPE=GPENTRY", "TRMIDNT=S001"],
                "facts": [
                    {"channel": "csd_resources", "type": "TERMINAL", "name": "S001", "group": "DFHTCT01"},
                ],
            },
            {
                "op": "DFHTCT",
                "operands": ["TYPE=GPENTRY", "TRMIDNT=S002"],
                "facts": [
                    {"channel": "csd_resources", "type": "TERMINAL", "name": "S002", "group": "DFHTCT01"},
                ],
            },
            # DFHMCT: TYPE=EMP vs refused TYPE=RECORD
            {
                "op": "DFHMCT",
                "operands": ["TYPE=EMP", "CLASS=PERFORM", "ID=(PP,4)"],
                "facts": [{"channel": "csd_resources", "type": "MONITORPOINT", "name": "USER.203", "group": "DFHMCT"}],
            },
            {"op": "DFHMCT", "operands": ["TYPE=RECORD", "CLASS=PERFORM", "EXCLUDE=(DFHTASK)"]},
            # DFHPLT: TYPE=ENTRY,PROGRAM=(...) + refused PROGRAM=DFHDELIM stage delimiter
            {"op": "DFHPLT", "operands": ["TYPE=INITIAL", "SUFFIX=I1"]},
            {
                "op": "DFHPLT",
                "operands": ["TYPE=ENTRY", "PROGRAM=(SHPPLT1,SHPPLT2)"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "PLT",
                        "name": "SHPPLT1",
                        "group": "DFHPLTI1",
                        "program": "SHPPLT1",
                    },
                    {
                        "channel": "csd_resources",
                        "type": "PLT",
                        "name": "SHPPLT2",
                        "group": "DFHPLTI1",
                        "program": "SHPPLT2",
                    },
                ],
            },
            {
                "op": "DFHPLT",
                "operands": ["TYPE=ENTRY", "PROGRAM=DFHDELIM"],
                "phantoms": [
                    {
                        "channel": "csd_resources",
                        "type": "PLT",
                        "name": "DFHDELIM",
                        "why": "DFHPLT PROGRAM=DFHDELIM is a pass delimiter between PLTPI/PLTSD stages, not a program",
                    }
                ],
            },
            {
                "op": "DFHPLT",
                "operands": ["TYPE=ENTRY", "PROGRAM=SHPPLT3"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "PLT",
                        "name": "SHPPLT3",
                        "group": "DFHPLTI1",
                        "program": "SHPPLT3",
                    }
                ],
            },
            # DSNCRCT: TYPE=INIT -> DB2CONN, refused TYPE=COMD & TYPE=POOL, TYPE=GROUP + TYPE=ENTRY -> DB2ENTRY
            {
                "op": "DSNCRCT",
                "operands": ["TYPE=INIT", "SUFFIX=01", "SUBID=DB2S", "PLANI=SHPDEFPL", "THRDMAX=12"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "DB2CONN",
                        "name": "DFHRCT01",
                        "group": "DFHRCT01",
                        "plan": "SHPDEFPL",
                    }
                ],
            },
            {"op": "DSNCRCT", "operands": ["TYPE=COMD", "AUTH=USERID", "THRDM=1", "THRDA=1"]},
            {"op": "DSNCRCT", "operands": ["TYPE=POOL", "PLAN=SHPPOOLP", "THRDM=3", "THRDA=3"]},
            {"op": "DSNCRCT", "operands": ["TYPE=GROUP", "GROUP=SHPDB2G"]},
            {
                "op": "DSNCRCT",
                "operands": ["TYPE=ENTRY", "TXID=(SHPI)", "PLAN=SHPINQPL", "THRDA=4", "TWAIT=POOL"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "DB2ENTRY",
                        "name": "SHPI",
                        "group": "SHPDB2G",
                        "plan": "SHPINQPL",
                        "transid": "SHPI",
                    }
                ],
            },
            {
                "op": "DSNCRCT",
                "operands": ["TYPE=ENTRY", "TXID=(SHPM)", "THRDA=2", "TWAIT=YES"],
                "facts": [
                    {
                        "channel": "csd_resources",
                        "type": "DB2ENTRY",
                        "name": "SHPM",
                        "group": "SHPDB2G",
                        "plan": "SHPDEFPL",
                        "transid": "SHPM",
                    }
                ],
            },
            # DFHSIT: TYPE=CSECT,SUFFIX=6$
            {
                "op": "DFHSIT",
                "operands": ["TYPE=CSECT", "SUFFIX=6$", "FCT=01", "DCT=01", "PCT=01", "PPT=01"],
                "facts": [{"channel": "csd_resources", "type": "SIT", "name": "DFHSIT6$", "group": "DFHSIT6$"}],
            },
            {"op": "DFHFCT", "operands": ["TYPE=FINAL"]},
        ],
    }
]

APP = {
    "id": "SHIP",
    "era": 2,
    "era_evidence": "SHPINQ/SHPRATE use COBOL-85 END-IF with command-level CICS XCTL/LINK; SHPGRP is an RDO CSD",
    "title": "Shipment inquiry (CICS, an incomplete export)",
    "style": "CICS; XCTL / LINK / CSD entries for programs the export lacks; a dead fork; HLASM macro tables",
    "copybooks": COPYBOOKS,
    "programs": [SHPINQ, SHPINQO, SHPRATE],
    "csd": CSD,
    "macro_tables": MACRO_TABLES,
}
