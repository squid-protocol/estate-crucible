"""shared/ -- the estate-wide libraries every app concatenates after its own."""

from .data import I

COPYLIB = [
    {
        "member": "DATEWS",
        "header": [" DATEWS   - STANDARD DATE / TIME WORK AREA (16 BYTES)"],
        "items": [
            I(5, "WS-CURR-DATE", "9(8)"),
            I(5, "WS-CURR-DATE-R", redefines="WS-CURR-DATE",
              kids=[I(10, "WS-CURR-YYYY", "9(4)"), I(10, "WS-CURR-MM", "99"), I(10, "WS-CURR-DD", "99")]),
            I(5, "WS-CURR-TIME", "9(8)"),
        ],
    },
]

# the enterprise-standard order record (ORDR keeps its own, newer one: H-0052)
ORDREC = {
    "member": "ORDREC",
    "header": [" ORDREC   - ENTERPRISE STANDARD ORDER RECORD (35 BYTES)"],
    "horror": "H-0052",
    "items": [
        I(5, "ORD-ID", "X(10)"), I(5, "ORD-CUST", "X(8)"), I(5, "ORD-ITEM", "X(12)"),
        I(5, "ORD-QTY", "S9(5)", "COMP-3"),
        I(5, "ORD-STATUS", "X", kids=[I(88, "ORD-OPEN", value="'O'"), I(88, "ORD-REJECTED", value="'R'")]),
        I(5, "FILLER", "X(2)"),
    ],
}
COPYLIB.append(ORDREC)

# the enterprise address record (TAXR keeps its own with a longer postal code: H-0052)
COPYLIB.append({
    "member": "ADDRREC",
    "header": [" ADDRREC  - ENTERPRISE STANDARD ADDRESS (5-CHAR POSTAL CODE)"],
    "horror": "H-0052",
    "items": [I(5, "ADR-LINE1", "X(30)"), I(5, "ADR-CITY", "X(20)"), I(5, "ADR-STATE", "X(2)"),
              I(5, "ADR-POSTAL", "X(5)")],
})

PROCLIB = [
    {
        "name": "AUDLOG",
        "steps": [
            {"name": "LOG", "pgm": "IEBGENER", "dds": [
                {"name": "SYSPRINT", "sysout": "*"},
                {"name": "SYSUT1", "dsn": "PROD.SHARED.AUDIT.STAGE", "disp": ("SHR",)},
                {"name": "SYSUT2", "dsn": "PROD.SHARED.AUDIT.LOG", "disp": ("MOD", "KEEP")},
            ]},
        ],
    },
]

SHARED = {"copylib": COPYLIB, "proclib": PROCLIB}
