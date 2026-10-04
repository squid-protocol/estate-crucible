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
