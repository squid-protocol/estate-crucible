"""AIXA -- Alternate Index Archipelago, the second Open World level estate (gitgalaxy#7065, #4894 VSAM).
An order shop that keeps its orders in a KSDS with an alternate index, its pick slots in an RRDS and its
audit log in an ESDS. The COBOL is small; the subject is how a SELECT, an IDCAMS card and a DD name the same
data set, and what file status each access ends in.

Planted: H-0076 (ALTERNATE RECORD KEY ... WITH DUPLICATES), H-0077 (RELATIVE KEY over an RRDS), H-0078 (a
SELECT over an ESDS: ORGANIZATION IS SEQUENTIAL), H-0079 (IDCAMS DEFINE ALTERNATEINDEX / DEFINE PATH /
BLDINDEX), H-0080 (a DD that names the PATH), H-0081 (file status 02 / 22 / 23 handled in a paragraph),
H-0082 (DEFINE CLUSTER in its three kinds: INDEXED, NUMBERED, NONINDEXED)."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw, read

H76, H77, H78, H79, H80, H81, H82 = "H-0076", "H-0077", "H-0078", "H-0079", "H-0080", "H-0081", "H-0082"

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
]

APP = {
    "id": "AIXA",
    "era": 2,
    "era_evidence": "END-IF and END-READ (COBOL-85); the JCL is IDCAMS and plain EXEC steps",
    "title": "Alternate Index Archipelago (VSAM organizations and access paths)",
    "style": "VSAM KSDS with an alternate index, RRDS, ESDS: SELECT clauses, IDCAMS cards, the PATH DD, file status",
    "copybooks": [],
    "dclgen": [],
    "programs": [AIXAKSD, AIXARRD, AIXAESD],
    "jcl": JOBS,
    "procs": [],
}
