"""AIXA -- Alternate Index Archipelago, the second Open World level estate (gitgalaxy#7065, #4894 VSAM).
An order shop that keeps its orders in a KSDS with an alternate index, its pick slots in an RRDS and its
audit log in an ESDS. The COBOL is small; the subject is how a SELECT, an IDCAMS card and a DD name the same
data set, and what file status each access ends in.

Planted: H-0076 (ALTERNATE RECORD KEY ... WITH DUPLICATES), H-0077 (RELATIVE KEY over an RRDS), H-0078 (a
SELECT over an ESDS: ORGANIZATION IS SEQUENTIAL), H-0079 (IDCAMS DEFINE ALTERNATEINDEX / DEFINE PATH /
BLDINDEX), H-0080 (a DD that names the PATH), H-0081 (file status 02 / 22 / 23 handled in a paragraph),
H-0082 (DEFINE CLUSTER in its three kinds: INDEXED, NUMBERED, NONINDEXED).
Slice 1 adds H-0106 (an RRDS read ACCESS SEQUENTIAL with START and written ACCESS RANDOM with REWRITE / DELETE),
H-0107 (an ESDS opened I-O: READ then REWRITE) and H-0108 (a KSDS with a unique and a duplicate alternate key,
UNIQUEKEY and NONUNIQUEKEY alternate indexes, one PATH DD each).
Slice 2 adds H-0109 (EXEC CICS READ with RIDFLD naming a relative byte address, RBA, on an ESDS and a relative
record number, RRN, on an RRDS)."""

from ..data import I
from ..stmt import cics, goback, if_, para, perform, raw, read

H76, H77, H78, H79, H80, H81, H82 = "H-0076", "H-0077", "H-0078", "H-0079", "H-0080", "H-0081", "H-0082"
H106, H107, H108, H109, H110 = "H-0106", "H-0107", "H-0108", "H-0109", "H-0110"

AIXAKSD = {
    "member": "AIXAKSD",
    "era": 2,
    "era_evidence": "END-IF and END-READ (COBOL-85); no later construct",
    "program_id": "AIXAKSD",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXAKSD - ORDERS IN A KSDS WITH AN ALTERNATE KEY.",
                "THE ALTERNATE INDEX IS REACHED BY PATH, DD ORDKSD1."],
    "selects": [{"name": "ORD-FILE", "assign": "ORDKSD", "status": "WS-ORD-STATUS", "org": "INDEXED",
                 "access": "DYNAMIC", "record_key": "ORD-ID",
                 "alternate_keys": [{"name": "ORD-CUST", "duplicates": True}], "horror": H76}],
    "fds": [{"fd": "ORD-FILE", "record": I(1, "ORD-REC", kids=[
        I(5, "ORD-ID", "X(8)"), I(5, "ORD-CUST", "X(8)"), I(5, "ORD-AMT", "9(7)"), I(5, "FILLER", "X(17)")])}],
    "ws": [
        I(1, "WS-ORD-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-HITS", "9(5)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN I-O ORD-FILE"),
             if_("WS-ORD-STATUS NOT = '00'",
                 [raw("DISPLAY 'AIXAKSD OPEN FAILED ' WS-ORD-STATUS", "MOVE 12 TO RETURN-CODE"), goback()]),
             perform("1000-ADD"),
             perform("2000-BROWSE"),
             perform("3000-PROBE"),
             raw("CLOSE ORD-FILE", "DISPLAY 'AIXAKSD HITS ' WS-HITS"),
             goback()),
        para("1000-ADD",
             raw("MOVE 'ORD00001' TO ORD-ID", "MOVE 'CUST0001' TO ORD-CUST", "MOVE 100 TO ORD-AMT",
                 "WRITE ORD-REC"),
             perform("9000-STATUS"),
             raw("MOVE 'ORD00002' TO ORD-ID", "WRITE ORD-REC"),
             perform("9000-STATUS"),
             raw("MOVE 'ORD00001' TO ORD-ID", "WRITE ORD-REC"),
             perform("9000-STATUS")),
        para("2000-BROWSE",
             raw("MOVE 'CUST0001' TO ORD-CUST",
                 "START ORD-FILE KEY IS EQUAL TO ORD-CUST",
                 "    INVALID KEY SET WS-EOF TO TRUE",
                 "END-START"),
             perform("2100-NEXT", until="WS-EOF")),
        para("2100-NEXT",
             raw("READ ORD-FILE NEXT RECORD", "    AT END SET WS-EOF TO TRUE", "END-READ"),
             if_("WS-ORD-STATUS > '02'", [raw("SET WS-EOF TO TRUE")]),
             if_("NOT WS-EOF",
                 [if_("ORD-CUST = 'CUST0001'", [raw("ADD 1 TO WS-HITS")], [raw("SET WS-EOF TO TRUE")])])),
        para("3000-PROBE",
             raw("MOVE 'ORD99999' TO ORD-ID",
                 "READ ORD-FILE KEY IS ORD-ID", "    INVALID KEY CONTINUE", "END-READ"),
             perform("9000-STATUS")),
        para("9000-STATUS",
             if_("WS-ORD-STATUS = '23'", [raw("DISPLAY 'ORDER NOT FOUND'")],
                 [if_("WS-ORD-STATUS = '02'", [raw("DISPLAY 'DUPLICATE ALTERNATE KEY'")],
                      [if_("WS-ORD-STATUS = '22'", [raw("DISPLAY 'DUPLICATE PRIME KEY'")])])]),
             horror=H81),
    ],
}

AIXARRD = {
    "member": "AIXARRD",
    "era": 2,
    "era_evidence": "END-IF (COBOL-85); no later construct",
    "program_id": "AIXARRD",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXARRD - PICK SLOTS IN AN RRDS, BY RELATIVE NUMBER."],
    "selects": [{"name": "SLOT-FILE", "assign": "SLOTS", "status": "WS-SLOT-STATUS", "org": "RELATIVE",
                 "access": "DYNAMIC", "relative_key": "WS-SLOT-NO", "horror": H77}],
    "fds": [{"fd": "SLOT-FILE", "record": I(1, "SLOT-REC", kids=[
        I(5, "SLOT-ID", "X(8)"), I(5, "SLOT-QTY", "9(5)"), I(5, "FILLER", "X(27)")])}],
    "ws": [
        I(1, "WS-SLOT-STATUS", "X(2)"),
        I(1, "WS-SLOT-NO", "9(4)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN I-O SLOT-FILE"),
             perform("1000-PUT"),
             raw("CLOSE SLOT-FILE"),
             goback()),
        para("1000-PUT",
             raw("MOVE 3 TO WS-SLOT-NO", "MOVE 'SLOT0003' TO SLOT-ID", "MOVE 12 TO SLOT-QTY",
                 "WRITE SLOT-REC", "    INVALID KEY DISPLAY 'SLOT TAKEN'", "END-WRITE",
                 "MOVE 9 TO WS-SLOT-NO",
                 "READ SLOT-FILE", "    INVALID KEY DISPLAY 'SLOT EMPTY'", "END-READ"),
             if_("WS-SLOT-STATUS = '23'", [raw("MOVE 4 TO RETURN-CODE")])),
    ],
}

AIXAESD = {
    "member": "AIXAESD",
    "era": 2,
    "era_evidence": "END-READ (COBOL-85); no later construct",
    "program_id": "AIXAESD",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXAESD - AUDIT LOG IN AN ESDS."],
    "selects": [{"name": "LOG-FILE", "assign": "LOGESD", "status": "WS-LOG-STATUS", "org": "SEQUENTIAL",
                 "access": "SEQUENTIAL", "horror": H78}],
    "fds": [{"fd": "LOG-FILE", "record": I(1, "LOG-REC", kids=[
        I(5, "LOG-TS", "X(14)"), I(5, "LOG-TEXT", "X(40)"), I(5, "FILLER", "X(6)")])}],
    "ws": [
        I(1, "WS-LOG-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-COUNT", "9(5)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN EXTEND LOG-FILE"),
             perform("1000-APPEND"),
             raw("CLOSE LOG-FILE", "OPEN INPUT LOG-FILE"),
             perform("8000-READ"),
             perform("2000-COUNT", until="WS-EOF"),
             raw("CLOSE LOG-FILE", "DISPLAY 'AIXAESD RECORDS ' WS-COUNT"),
             goback()),
        para("1000-APPEND",
             raw("MOVE '20261031120000' TO LOG-TS", "MOVE 'ORDER ORD00001 ACCEPTED' TO LOG-TEXT",
                 "WRITE LOG-REC")),
        para("2000-COUNT",
             raw("ADD 1 TO WS-COUNT"),
             perform("8000-READ")),
        para("8000-READ",
             read("LOG-FILE", at_end=[raw("SET WS-EOF TO TRUE")])),
    ],
}

AIXARRS = {
    "member": "AIXARRS",
    "era": 2,
    "era_evidence": "END-START, END-READ, END-WRITE, END-REWRITE, END-DELETE (COBOL-85); no later construct",
    "program_id": "AIXARRS",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXARRS - COPY PICK SLOTS TO A HISTORY RRDS.",
                "IN BY SEQUENCE FROM SLOT 5, OUT BY NUMBER."],
    "selects": [
        {"name": "SLOT-IN", "assign": "SLOTIN", "status": "WS-IN-STATUS", "org": "RELATIVE",
         "access": "SEQUENTIAL", "relative_key": "WS-IN-NO", "horror": H106},
        {"name": "SLOT-OUT", "assign": "SLOTOUT", "status": "WS-OUT-STATUS", "org": "RELATIVE",
         "access": "RANDOM", "relative_key": "WS-OUT-NO", "horror": H106},
    ],
    "fds": [
        {"fd": "SLOT-IN", "record": I(1, "IN-REC", kids=[
            I(5, "IN-ID", "X(8)"), I(5, "IN-QTY", "9(5)"), I(5, "FILLER", "X(27)")])},
        {"fd": "SLOT-OUT", "record": I(1, "OUT-REC", kids=[
            I(5, "OUT-ID", "X(8)"), I(5, "OUT-QTY", "9(5)"), I(5, "FILLER", "X(27)")])},
    ],
    "ws": [
        I(1, "WS-IN-STATUS", "X(2)"),
        I(1, "WS-OUT-STATUS", "X(2)"),
        I(1, "WS-IN-NO", "9(4)", value="ZERO"),
        I(1, "WS-OUT-NO", "9(4)", value="ZERO"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-COPIED", "9(5)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN INPUT SLOT-IN", "OPEN I-O SLOT-OUT"),
             perform("1000-POSITION"),
             perform("2000-COPY", until="WS-EOF"),
             perform("3000-TRIM"),
             raw("CLOSE SLOT-IN", "CLOSE SLOT-OUT", "DISPLAY 'AIXARRS COPIED ' WS-COPIED"),
             goback()),
        para("1000-POSITION",
             raw("MOVE 5 TO WS-IN-NO",
                 "START SLOT-IN KEY IS NOT LESS THAN WS-IN-NO",
                 "    INVALID KEY SET WS-EOF TO TRUE",
                 "END-START")),
        para("2000-COPY",
             raw("READ SLOT-IN", "    AT END SET WS-EOF TO TRUE", "END-READ"),
             if_("NOT WS-EOF",
                 [raw("MOVE IN-REC TO OUT-REC", "MOVE WS-IN-NO TO WS-OUT-NO",
                      "WRITE OUT-REC", "    INVALID KEY PERFORM 2100-REPLACE", "END-WRITE",
                      "ADD 1 TO WS-COPIED")])),
        para("2100-REPLACE",
             raw("REWRITE OUT-REC", "    INVALID KEY DISPLAY 'SLOT LOST ' WS-OUT-NO", "END-REWRITE")),
        para("3000-TRIM",
             raw("MOVE 99 TO WS-OUT-NO",
                 "DELETE SLOT-OUT RECORD", "    INVALID KEY DISPLAY 'SLOT 99 NOT THERE'", "END-DELETE")),
    ],
}

AIXAESU = {
    "member": "AIXAESU",
    "era": 2,
    "era_evidence": "END-READ (COBOL-85); no later construct",
    "program_id": "AIXAESU",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXAESU - MARK LOG RECORDS REVIEWED.",
                "AN ESDS RECORD KEEPS ITS LENGTH; NO DELETE."],
    "selects": [{"name": "LOG-FILE", "assign": "LOGUPD", "status": "WS-LOG-STATUS", "org": "SEQUENTIAL",
                 "access": "SEQUENTIAL", "horror": H107}],
    "fds": [{"fd": "LOG-FILE", "record": I(1, "LOG-REC", kids=[
        I(5, "LOG-TS", "X(14)"), I(5, "LOG-TEXT", "X(40)"), I(5, "FILLER", "X(6)")])}],
    "ws": [
        I(1, "WS-LOG-STATUS", "X(2)"),
        I(1, "WS-EOF-FLAG", "X", value="'N'", kids=[I(88, "WS-EOF", value="'Y'")]),
        I(1, "WS-MARKED", "9(5)", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN I-O LOG-FILE"),
             perform("8000-READ"),
             perform("1000-MARK", until="WS-EOF"),
             raw("CLOSE LOG-FILE", "DISPLAY 'AIXAESU MARKED ' WS-MARKED"),
             goback()),
        para("1000-MARK",
             if_("LOG-TEXT = 'ORDER ORD00001 ACCEPTED'",
                 [raw("MOVE 'ORDER ORD00001 REVIEWED' TO LOG-TEXT",
                      "REWRITE LOG-REC", "ADD 1 TO WS-MARKED")]),
             perform("8000-READ"),
             horror=H107),
        para("8000-READ",
             read("LOG-FILE", at_end=[raw("SET WS-EOF TO TRUE")])),
    ],
}

AIXAKS2 = {
    "member": "AIXAKS2",
    "era": 2,
    "era_evidence": "END-IF and END-READ (COBOL-85); no later construct",
    "program_id": "AIXAKS2",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXAKS2 - CUSTOMERS, TWO ALTERNATE KEYS.",
                "TAX ID IS UNIQUE, NAME MAY REPEAT."],
    "selects": [{"name": "CUS-FILE", "assign": "CUSKSD", "status": "WS-CUS-STATUS", "org": "INDEXED",
                 "access": "DYNAMIC", "record_key": "CUS-ID",
                 "alternate_keys": [{"name": "CUS-TAX", "duplicates": False},
                                    {"name": "CUS-NAME", "duplicates": True}], "horror": H108}],
    "fds": [{"fd": "CUS-FILE", "record": I(1, "CUS-REC", kids=[
        I(5, "CUS-ID", "X(8)"), I(5, "CUS-TAX", "X(9)"), I(5, "CUS-NAME", "X(20)"), I(5, "FILLER", "X(3)")])}],
    "ws": [
        I(1, "WS-CUS-STATUS", "X(2)"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN I-O CUS-FILE"),
             if_("WS-CUS-STATUS NOT = '00'",
                 [raw("DISPLAY 'AIXAKS2 OPEN FAILED ' WS-CUS-STATUS", "MOVE 12 TO RETURN-CODE"), goback()]),
             perform("1000-ADD"),
             perform("2000-PROBE"),
             raw("CLOSE CUS-FILE"),
             goback()),
        para("1000-ADD",
             raw("MOVE 'CUS00001' TO CUS-ID", "MOVE '123456789' TO CUS-TAX", "MOVE 'SMITH' TO CUS-NAME",
                 "WRITE CUS-REC"),
             perform("9000-STATUS"),
             raw("MOVE 'CUS00002' TO CUS-ID", "MOVE '987654321' TO CUS-TAX", "WRITE CUS-REC"),
             perform("9000-STATUS"),
             raw("MOVE 'CUS00003' TO CUS-ID", "MOVE '123456789' TO CUS-TAX", "WRITE CUS-REC"),
             perform("9000-STATUS")),
        para("2000-PROBE",
             raw("MOVE '987654321' TO CUS-TAX",
                 "READ CUS-FILE KEY IS CUS-TAX", "    INVALID KEY DISPLAY 'TAX ID NOT FOUND'", "END-READ"),
             perform("9000-STATUS")),
        para("9000-STATUS",
             if_("WS-CUS-STATUS = '22'", [raw("DISPLAY 'DUPLICATE KEY ' CUS-ID")]),
             if_("WS-CUS-STATUS = '02'", [raw("DISPLAY 'DUPLICATE NAME ' CUS-NAME")]),
             horror=H108),
    ],
}

AIXACIC = {
    "member": "AIXACIC",
    "era": 2,
    "era_evidence": "EXEC CICS ... RESP() and END-IF (COBOL-85) (#5117 era 2)",
    "program_id": "AIXACIC",
    "author": "ORDER SYSTEMS",
    "remarks": ["AIXACIC - ONLINE LOOKUP (TRANSACTION AXLK).",
                "AUDIT LOG RECORD BY BYTE ADDRESS, PICK SLOT BY RECORD NUMBER."],
    "compile": "compiled-stubbed",
    "ws": [
        I(1, "WS-LOG-REC", kids=[
            I(5, "WL-TS", "X(14)"), I(5, "WL-TEXT", "X(40)"), I(5, "FILLER", "X(6)")]),
        I(1, "WS-SLOT-REC", kids=[
            I(5, "WSL-ID", "X(8)"), I(5, "WSL-QTY", "9(5)"), I(5, "FILLER", "X(27)")]),
        I(1, "WS-LOG-RBA", "S9(8)", "COMP", value="ZERO"),
        I(1, "WS-SLOT-RRN", "S9(8)", "COMP", value="ZERO"),
        I(1, "WS-RESP", "S9(8)", "COMP"),
    ],
    "units": [
        para("0000-MAIN",
             perform("1000-LOG-BY-RBA"),
             perform("2000-SLOT-BY-RRN"),
             cics("RETURN")),
        para("1000-LOG-BY-RBA",
             raw("MOVE ZERO TO WS-LOG-RBA"),
             cics("READ FILE('AIXALOG') INTO(WS-LOG-REC)", "RIDFLD(WS-LOG-RBA) RBA",
                  "RESP(WS-RESP)", horror=H109,
                  resource={"verb": "READ", "kind": "FILE", "name": "AIXALOG", "record": "WS-LOG-REC",
                            "access": "read"}),
             if_("WS-RESP NOT = 0", [raw("MOVE 4 TO RETURN-CODE")])),
        para("2000-SLOT-BY-RRN",
             raw("MOVE 3 TO WS-SLOT-RRN"),
             cics("READ FILE('AIXASLT') INTO(WS-SLOT-REC)", "RIDFLD(WS-SLOT-RRN) RRN",
                  "RESP(WS-RESP)", horror=H109,
                  resource={"verb": "READ", "kind": "FILE", "name": "AIXASLT", "record": "WS-SLOT-REC",
                            "access": "read"}),
             if_("WS-RESP NOT = 0", [raw("MOVE 4 TO RETURN-CODE")])),
    ],
}

CSD = [
    {
        "group": "AIXAGRP",
        "era": 2,
        "era_evidence": "CSD DEFINE PROGRAM / TRANSACTION / FILE is RDO (CICS/MVS 2.x, #5117 era 2)",
        "title": "ORDER SYSTEMS",
        "defines": [
            ("PROGRAM", "AIXACIC", {"LANGUAGE": "COBOL"}),
            ("TRANSACTION", "AXLK", {"PROGRAM": "AIXACIC"}),
            ("FILE", "AIXALOG", {"DSNAME": "PROD.AIXA.LOG"}),
            ("FILE", "AIXASLT", {"DSNAME": "PROD.AIXA.SLOTS"}),
        ],
    },
]


def _dd(name, dsn=None, disp=("SHR",), **kw):
    return {"name": name, "dsn": dsn, "disp": disp, **kw}


LOADLIB = "PROD.AIXA.LOADLIB"
JOBS = [
    {
        # one IDCAMS step defines the three kinds of cluster, then the alternate index, its path, and builds it
        "name": "AIXADEF",
        "title": "AIXA DEFINE VSAM",
        "accounting": "(AIXA,0100)",
        "comments": ["DEFINE THE ORDER KSDS, ITS ALTERNATE INDEX AND PATH, THE SLOT RRDS AND THE LOG ESDS"],
        "steps": [
            {"name": "IDC010", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H82, "inline": [
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.ORDER) -",
                                "        INDEXED KEYS(8 0) RECORDSIZE(40 40) -",
                                "        CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.SLOTS) -",
                                "        NUMBERED RECORDSIZE(40 40) -",
                                "        CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.LOG) -",
                                "        NONINDEXED RECORDSIZE(60 60) -",
                                "        CYLINDERS(1 1))"]),
                ]},
            ]},
            {"name": "IDC020", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H79, "inline": [
                    ("DEFINE", [" DEFINE ALTERNATEINDEX (NAME(PROD.AIXA.ORDER.AIX) -",
                                "        RELATE(PROD.AIXA.ORDER) KEYS(8 8) -",
                                "        NONUNIQUEKEY UPGRADE CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE PATH (NAME(PROD.AIXA.ORDER.PATH) -",
                                "        PATHENTRY(PROD.AIXA.ORDER.AIX) UPDATE)"]),
                    ("BLDINDEX", [" BLDINDEX INDATASET(PROD.AIXA.ORDER) -",
                                  "        OUTDATASET(PROD.AIXA.ORDER.AIX)"]),
                ]},
            ]},
        ],
    },
    {
        # the order program: the base cluster by one DD, the PATH over the alternate index by the next
        "name": "AIXARUN",
        "title": "AIXA ORDER RUN",
        "accounting": "(AIXA,0100)",
        "steps": [
            {"name": "KSD010", "pgm": "AIXAKSD", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("ORDKSD", "PROD.AIXA.ORDER", ("OLD",)),
                _dd("ORDKSD1", "PROD.AIXA.ORDER.PATH", ("OLD",), horror=H80),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "RRD020", "pgm": "AIXARRD", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("SLOTS", "PROD.AIXA.SLOTS", ("OLD",)),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "ESD030", "pgm": "AIXAESD", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("LOGESD", "PROD.AIXA.LOG", ("OLD",)),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
    {
        # slice 1: the history RRDS, the customer KSDS with a unique and a duplicate alternate key
        "name": "AIXADF2",
        "title": "AIXA DEFINE VSAM 2",
        "accounting": "(AIXA,0100)",
        "comments": ["DEFINE THE HISTORY RRDS, THE CUSTOMER KSDS, TWO ALTERNATE INDEXES AND THEIR PATHS"],
        "steps": [
            {"name": "IDC010", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H106, "inline": [
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.SLOTH) -",
                                "        NUMBERED RECORDSIZE(40 40) -",
                                "        CYLINDERS(1 1))"]),
                ]},
            ]},
            {"name": "IDC020", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H108, "inline": [
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.CUST) -",
                                "        INDEXED KEYS(8 0) RECORDSIZE(40 40) -",
                                "        CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE ALTERNATEINDEX (NAME(PROD.AIXA.CUST.TAXAIX) -",
                                "        RELATE(PROD.AIXA.CUST) KEYS(9 8) -",
                                "        UNIQUEKEY UPGRADE CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE ALTERNATEINDEX (NAME(PROD.AIXA.CUST.NAMAIX) -",
                                "        RELATE(PROD.AIXA.CUST) KEYS(20 17) -",
                                "        NONUNIQUEKEY UPGRADE CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE PATH (NAME(PROD.AIXA.CUST.TAXPATH) -",
                                "        PATHENTRY(PROD.AIXA.CUST.TAXAIX) UPDATE)"]),
                    ("DEFINE", [" DEFINE PATH (NAME(PROD.AIXA.CUST.NAMPATH) -",
                                "        PATHENTRY(PROD.AIXA.CUST.NAMAIX) UPDATE)"]),
                    ("BLDINDEX", [" BLDINDEX INDATASET(PROD.AIXA.CUST) -",
                                  "        OUTDATASET(PROD.AIXA.CUST.TAXAIX)"]),
                    ("BLDINDEX", [" BLDINDEX INDATASET(PROD.AIXA.CUST) -",
                                  "        OUTDATASET(PROD.AIXA.CUST.NAMAIX)"]),
                ]},
            ]},
        ],
    },
    {
        # slice 1: the RRDS copy, the in-place ESDS update, the two-alternate-key KSDS, a PATH DD per key
        "name": "AIXARU2",
        "title": "AIXA ORDER RUN 2",
        "accounting": "(AIXA,0100)",
        "steps": [
            {"name": "RRS010", "pgm": "AIXARRS", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("SLOTIN", "PROD.AIXA.SLOTS", ("OLD",)),
                _dd("SLOTOUT", "PROD.AIXA.SLOTH", ("OLD",)),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "ESU020", "pgm": "AIXAESU", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("LOGUPD", "PROD.AIXA.LOG", ("OLD",)),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "KS2030", "pgm": "AIXAKS2", "dds": [
                _dd("STEPLIB", LOADLIB),
                _dd("CUSKSD", "PROD.AIXA.CUST", ("OLD",)),
                _dd("CUSKSD1", "PROD.AIXA.CUST.TAXPATH", ("OLD",), horror=H108),
                _dd("CUSKSD2", "PROD.AIXA.CUST.NAMPATH", ("OLD",), horror=H108),
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
    {
        # slice 3: a LINEAR data set and a zFS aggregate; neither has records, so no KEYS and no RECORDSIZE
        "name": "AIXADF3",
        "title": "AIXA DEFINE LINEAR ZFS",
        "accounting": "(AIXA,0100)",
        "comments": ["DEFINE THE LINEAR EXTRACT DATA SET AND THE ZFS AGGREGATE FOR THE ORDER REPORTS"],
        "steps": [
            {"name": "IDC010", "pgm": "IDCAMS", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSIN", "horror": H110, "inline": [
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.EXTRACT) -",
                                "        LINEAR CONTROLINTERVALSIZE(4096) -",
                                "        CYLINDERS(1 1))"]),
                    ("DEFINE", [" DEFINE CLUSTER (NAME(PROD.AIXA.REPORTS.ZFS) -",
                                "        ZFS CYLINDERS(5 1))"]),
                ]},
            ]},
        ],
    },
]

APP = {
    "id": "AIXA",
    "era": 2,
    "era_evidence": "END-IF and END-READ (COBOL-85); the JCL is IDCAMS and plain EXEC steps",
    "title": "Alternate Index Archipelago (VSAM organizations and access paths)",
    "style": "VSAM KSDS with an alternate index, RRDS, ESDS: SELECT clauses, IDCAMS cards, the PATH DD, file status",
    "copybooks": [],
    "dclgen": [],
    "programs": [AIXAKSD, AIXARRD, AIXAESD, AIXARRS, AIXAESU, AIXAKS2, AIXACIC],
    "csd": CSD,
    "jcl": JOBS,
    "procs": [],
}
