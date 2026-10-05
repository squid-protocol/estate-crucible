"""TAXR -- quarterly tax withholding (batch). The opposite fork from ORDR: TAXCALC2 replaced
TAXCALC in 2006 and is what the job runs; TAXCALC was never deleted. TAXR keeps its own
ADDRREC (a 10-character postal code) in front of the enterprise one, a retired copybook
in its OLD library, and a Y2K windowing paragraph nobody performs since 2000.

Planted: H-0051 (TAXCALC, dead), H-0052 (ADDRREC in TAXRCPY and SHRCPY), H-0054 (CALL of a
vendor module the estate lacks), H-0055 (8000-Y2K-WINDOW), H-0056 (TAXOLD)."""

import copy

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H51, H52, H54, H55, H56 = "H-0051", "H-0052", "H-0054", "H-0055", "H-0056"

COPYBOOKS = [
    {"member": "ADDRREC", "header": [" ADDRREC  - TAX ADDRESS (TAXR LOCAL COPY, 10-CHAR POSTAL CODE)"],
     "horror": H52,
     "items": [I(5, "ADR-LINE1", "X(30)"), I(5, "ADR-CITY", "X(20)"), I(5, "ADR-STATE", "X(2)"),
               I(5, "ADR-POSTAL", "X(10)")]},
    {"member": "TAXPARM", "header": [" TAXPARM  - WITHHOLDING PARAMETERS"],
     "items": [I(5, "TP-YEAR", "9(4)"), I(5, "TP-QTR", "9"), I(5, "TP-RATE", "9V9(4)", value="0.2200")]},
]

OLD_COPYBOOKS = [
    {"member": "TAXOLD", "header": [" TAXOLD   - 1999 WITHHOLDING TABLE. NO LONGER COPIED."],
     "orphan": "no COPY names TAXOLD; it sits only in the retired TAXROLD library", "orphan_horror": H56,
     "horror": H56,
     "items": [I(5, "TO-BRACKET", "9(7)", occurs=8), I(5, "TO-RATE", "9V99", occurs=8)]},
]

TAXCALC2 = {
    "member": "TAXCALC2",
    "program_id": "TAXCALC2",
    "numbered": True,
    "author": "J WEXLER",
    "date_written": "02/14/06",
    "remarks": ["TAXCALC2 - QUARTERLY WITHHOLDING. REPLACES TAXCALC (2006).", "RUN BY JOB TAXQTR."],
    "ws": [
        I(1, "WS-ADDRESS", copy=["ADDRREC"], horror=H52),
        I(1, "WS-PARM", copy=["TAXPARM"]),
        I(1, "WS-GROSS", "S9(9)V99", "COMP-3", value="ZERO"),
        I(1, "WS-TAX", "S9(9)V99", "COMP-3", value="ZERO"),
        I(1, "WS-YY", "99", value="ZERO"),
    ],
    "units": [
        para("0000-MAIN",
             perform("1000-CALC"),
             call("TAXVEND", using=["WS-ADDRESS", "WS-TAX"], horror=H54),
             goback()),
        para("1000-CALC",
             raw("COMPUTE WS-TAX ROUNDED = WS-GROSS * TP-RATE"),
             if_("ADR-STATE = 'NY'", [raw("ADD 1 TO WS-TAX")])),
        # windowed two-digit years before the 2000 conversion; nothing performs it
        para("8000-Y2K-WINDOW",
             if_("WS-YY < 50", [raw("COMPUTE TP-YEAR = 2000 + WS-YY")], [raw("COMPUTE TP-YEAR = 1900 + WS-YY")]),
             horror=H55,
             dead="no PERFORM or GO TO names it; 1000-CALC before it is reached only by PERFORM"),
    ],
}

# the original, replaced in 2006: a 5-character postal code and no vendor call
TAXCALC = copy.deepcopy(TAXCALC2)
TAXCALC.update({
    "member": "TAXCALC", "program_id": "TAXCALC", "program_id_horror": H51, "date_written": "07/01/91",
    "remarks": ["TAXCALC - QUARTERLY WITHHOLDING.", "REPLACED BY TAXCALC2 (2006). DO NOT RUN."],
    "dead": "replaced by TAXCALC2: no CALL or job step names TAXCALC", "dead_horror": H51,
})
TAXCALC["units"] = [para("0000-MAIN", perform("1000-CALC"), goback()), TAXCALC2["units"][1]]

JOBS = [
    {
        "name": "TAXQTR",
        "title": "TAX QUARTERLY",
        "accounting": "(TAXR,0601)",
        "steps": [
            {"name": "CALC", "pgm": "TAXCALC2", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.TAXR.LOADLIB", "disp": ("SHR",)},
                {"name": "STEPLIB2", "dsn": "VENDOR.TAXLINK.LOADLIB", "disp": ("SHR",)},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "TAXR",
    "title": "Tax withholding (V2 live, original dead)",
    "style": "numbered; a replaced original kept beside its V2; an app copybook shadowing the shared one",
    "copybooks": COPYBOOKS,
    "old_copybooks": OLD_COPYBOOKS,
    "programs": [TAXCALC, TAXCALC2],
    "jcl": JOBS,
}
