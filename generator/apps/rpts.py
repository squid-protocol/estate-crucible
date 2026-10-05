"""RPTS -- management reports. Report headings are long literals, continued past column 72
the way every reporting shop writes them.

Planted: H-0060 (gitgalaxy#4391)."""

from ..data import I
from ..stmt import goback, para, perform, raw

H60 = "H-0060"

HDR1 = "'ACME MANUFACTURING  -  MONTHLY OPERATIONS SUMMARY  -  CONFIDENTIAL'"
HDR2 = "'REGION   PLANT    UNITS BUILT    UNITS SHIPPED    BACKLOG  STATUS'"

RPTHDR = {
    "member": "RPTHDR",
    "program_id": "RPTHDR",
    "author": "MIS REPORTING",
    "date_written": "05/20/97",
    "remarks": ["RPTHDR - PRINT THE MONTHLY OPERATIONS HEADINGS."],
    "selects": [{"name": "RPT-FILE", "assign": "RPTOUT", "status": "WS-RPT-STATUS"}],
    "fds": [{"fd": "RPT-FILE", "record": I(1, "RPT-LINE", "X(80)")}],
    "ws": [
        I(1, "WS-RPT-STATUS", "X(2)"),
        I(1, "HDR-LINE-1", "X(80)", value=HDR1, continued=True, horror=H60),
        I(1, "HDR-LINE-2", "X(80)", value=HDR2, continued=True, horror=H60),
        I(1, "WS-PAGE", "9(4)", value="0"),
    ],
    "units": [
        para("0000-MAIN",
             raw("OPEN OUTPUT RPT-FILE"),
             perform("1000-HEADINGS"),
             raw("CLOSE RPT-FILE"),
             goback()),
        para("1000-HEADINGS",
             raw("ADD 1 TO WS-PAGE",
                 "WRITE RPT-LINE FROM HDR-LINE-1",
                 "WRITE RPT-LINE FROM HDR-LINE-2")),
    ],
}

JOBS = [
    {
        "name": "RPTMTH",
        "title": "MONTHLY OPS REPORT",
        "accounting": "(MIS,0597)",
        "steps": [
            {"name": "HEAD", "pgm": "RPTHDR", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.MIS.LOADLIB", "disp": ("SHR",)},
                {"name": "RPTOUT", "sysout": "A"},
            ]},
        ],
    },
]

APP = {
    "id": "RPTS",
    "title": "Management reports (continued literals)",
    "style": "report headings as VALUE literals continued past column 72",
    "programs": [RPTHDR],
    "jcl": JOBS,
}
