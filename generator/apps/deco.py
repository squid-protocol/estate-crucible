"""DECO -- a decommissioned application. Its programs were deleted in 2015; its job, its CSD
group and its record copybook were not. Every reference is an expected gap, and nothing
COPYs the copybook.

Planted: H-0054 (EXEC PGM, CSD PROGRAM and TRANSACTION of deleted programs), H-0056
(DECOREC)."""

from ..data import I

H54, H56 = "H-0054", "H-0056"

COPYBOOKS = [
    {"member": "DECOREC", "header": [" DECOREC  - DEALER COMMISSION RECORD (APPLICATION RETIRED 2015)"],
     "orphan": "the DECO programs that COPYed it were deleted in 2015", "orphan_horror": H56, "horror": H56,
     "items": [I(5, "DC-DEALER", "X(6)"), I(5, "DC-MONTH", "9(6)"), I(5, "DC-AMOUNT", "S9(7)V99", "COMP-3")]},
]

JOBS = [
    {
        "name": "DECOMTH",
        "title": "DEALER COMMISSION",
        "accounting": "(DECO,1501)",
        "comments": ["RETIRED 2015 - SCHEDULER ENTRY REMOVED, JOB KEPT FOR REFERENCE"],
        "steps": [
            {"name": "EXTRACT", "pgm": "DECOEXT", "horror": H54, "dds": [
                {"name": "STEPLIB", "dsn": "PROD.DECO.LOADLIB", "disp": ("SHR",)},
                {"name": "DEALERS", "dsn": "PROD.DECO.DEALERS", "disp": ("SHR",)},
            ]},
            {"name": "LOAD", "pgm": "DECOLOAD", "cond": "(0,NE)", "horror": H54, "dds": [
                {"name": "STEPLIB", "dsn": "PROD.DECO.LOADLIB", "disp": ("SHR",)},
                {"name": "COMMOUT", "dsn": "PROD.DECO.COMMISSN", "gen": "+1", "disp": ("NEW", "CATLG", "DELETE"),
                 "extra": ["SPACE=(TRK,(5,5))"]},
            ]},
        ],
    },
]

CSD = [
    {
        "group": "DECOGRP",
        "title": "DEALER COMMISSION INQUIRY (RETIRED)",
        "defines": [
            ("PROGRAM", "DECOINQ", {"LANGUAGE": "COBOL", "_horror": H54}),
            ("TRANSACTION", "DECI", {"PROGRAM": "DECOINQ", "_horror": H54}),
        ],
    },
]

APP = {
    "id": "DECO",
    "title": "Dealer commission (decommissioned)",
    "style": "no programs left: a job, a CSD group and a copybook that outlived them",
    "copybooks": COPYBOOKS,
    "jcl": JOBS,
    "csd": CSD,
}
