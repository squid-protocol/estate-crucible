"""PCED -- a pricing tool maintained on PCs and round-tripped through a git server. Its members
carry TABs and trailing white space, one is keyed in lower case, one is free format.

Planted: H-0058 (PCEDTAB), H-0059 (PCEDLOW)."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H58, H59 = "H-0058", "H-0059"

PCEDTAB = {
    "member": "PCEDTAB",
    "program_id": "PCEDTAB",
    "tabs": True,
    "member_horror": H58,
    "author": "PRICING TEAM",
    "remarks": ["PCEDTAB - PRICE TABLE LOAD. EDITED ON A PC."],
    "ws": [
        I(1, "WS-PRICES", kids=[I(5, "WS-PRICE", "S9(5)V99", "COMP-3", occurs=10)]),
        I(1, "WS-I", "S9(4)", "COMP", value="0"),
        I(1, "WS-TOTAL", "S9(7)V99", "COMP-3", value="0"),
    ],
    "units": [
        para("MAIN-PARA",
             perform("LOAD-TABLE"),
             call("PCEDLOW", using=["WS-TOTAL"]),
             goback()),
        para("LOAD-TABLE",
             raw("MOVE 1 TO WS-I"),
             perform("ADD-PRICE", until="WS-I > 10")),
        para("ADD-PRICE",
             raw("ADD WS-PRICE (WS-I) TO WS-TOTAL", "ADD 1 TO WS-I")),
    ],
}

PCEDLOW = {
    "member": "PCEDLOW",
    "program_id": "pcedlow",
    "lower": True,
    "member_horror": H59,
    "author": "pricing team",
    "remarks": ["pcedlow - round a price total. keyed in lower case."],
    "ws": [I(1, "ws-cents", "S9(9)", "COMP", value="0"),
           I(1, "ws-flag", "X", value="'n'", kids=[I(88, "ws-rounded", value="'y'")])],
    "linkage": [I(1, "lk-total", "S9(7)V99", "COMP-3")],
    "using": ["lk-total"],
    "units": [
        para("main-para",
             perform("round-total"),
             if_("ws-rounded", [raw("DISPLAY 'pcedlow rounded'")]),
             goback()),
        para("round-total",
             raw("COMPUTE ws-cents = lk-total * 100", "COMPUTE lk-total ROUNDED = ws-cents / 100",
                 "SET ws-rounded TO TRUE")),
    ],
}

PCEDFREE = {
    "member": "PCEDFREE",
    "program_id": "PCEDFREE",
    "free": True,
    "remarks": ["PCEDFREE - PRICE BAND REPORT, FREE FORMAT."],
    "ws": [I(1, "WS-BAND", kids=[I(5, "WS-LOW", "9(5)", value="0"), I(5, "WS-HIGH", "9(5)", value="99999")])],
    "units": [
        para("MAIN-PARA", perform("SHOW-BAND"), goback()),
        para("SHOW-BAND", raw("DISPLAY 'BAND ' WS-LOW ' - ' WS-HIGH")),
    ],
}

JOBS = [
    {
        "name": "PCEDLOAD",
        "title": "PRICE TABLE LOAD",
        "accounting": "(PCED,2201)",
        "steps": [
            {"name": "LOAD", "pgm": "PCEDTAB", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.PCED.LOADLIB", "disp": ("SHR",)},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
            {"name": "BANDS", "pgm": "PCEDFREE", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.PCED.LOADLIB", "disp": ("SHR",)},
            ]},
        ],
    },
]

APP = {
    "id": "PCED",
    "title": "Pricing tool (PC-edited members)",
    "style": "TABs and trailing white space, lower-case source, free format",
    "programs": [PCEDTAB, PCEDLOW, PCEDFREE],
    "jcl": JOBS,
}
