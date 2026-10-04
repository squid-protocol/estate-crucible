"""GULF -- an Arabic account inquiry. The BMS mapset is in EBCDIC cp420 (Arabic), its screen
text stored in visual order (right to left, as the 3270 shows it); the program is in cp037.

Planted: H-0045 (BiDi BMS in cp420)."""

from ..data import C
from ..stmt import cics, para, raw

H45 = "H-0045"

# "رقم الحساب" (account number) and "الاسم" (name), stored in visual order: reversed
ACCOUNT_LABEL = "رقم الحساب"[::-1]
NAME_LABEL = "الاسم"[::-1]

BMS = [
    {
        "mapset": "GULFMS",
        "horror": H45,
        "encoding": ("cp420", "nel"),
        "maps": [
            {"name": "GULFMAP", "size": (24, 80), "fields": [
                {"pos": (2, 60), "length": 10, "attrb": "ASKIP,NORM", "initial": ACCOUNT_LABEL},
                {"name": "ACCTNO", "pos": (2, 40), "length": 10, "attrb": "UNPROT,IC"},
                {"pos": (4, 70), "length": 5, "attrb": "ASKIP,NORM", "initial": NAME_LABEL},
                {"name": "CUSTNM", "pos": (4, 40), "length": 30, "attrb": "ASKIP,NORM"},
            ]},
        ],
    },
]

GULFINQ = {
    "member": "GULFINQ",
    "program_id": "GULFINQ",
    "author": "GULF BRANCH SYSTEMS",
    "remarks": ["GULFINQ - ACCOUNT INQUIRY ON AN ARABIC 3270 SCREEN."],
    "compile": "compiled-stubbed",
    "ws": [C("GULFMS")],
    "units": [
        para("0000-MAIN",
             raw("MOVE LOW-VALUES TO GULFMAPO"),
             cics("SEND MAP('GULFMAP') MAPSET('GULFMS') ERASE",
                  resource={"verb": "SEND", "kind": "MAP", "name": "GULFMAP", "qualifier": "GULFMS",
                            "access": "write"}),
             cics("RETURN")),
    ],
}

APP = {
    "id": "GULF",
    "title": "Arabic account inquiry (EBCDIC cp420 BMS)",
    "style": "BMS in cp420 with visual-order Arabic; program and symbolic map in cp037 FB80",
    "encodings": {"cobol": ("cp037", "fb80"), "copybook": ("cp037", "fb80")},
    "bms": BMS,
    "programs": [GULFINQ],
}
