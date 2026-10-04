"""MODN -- a modernised rate service. Free-format source (>>SOURCE FORMAT FREE): no
sequence area, no columns, data entries indented under their parents.

Planted: H-0028 (D040)."""

from ..data import I
from ..stmt import goback, if_, para, perform, raw

H28 = "H-0028"

MODRATE = {
    "member": "MODRATE",
    "program_id": "MODRATE",
    "free": True,
    "remarks": ["MODRATE - RATE LOOKUP, REWRITTEN IN FREE FORMAT."],
    "ws": [
        I(1, "VALUE-BYTES", horror=H28, kids=[I(5, "VB-CODE", "X(4)"), I(5, "VB-RATE", "9V9(4)")]),
        I(1, "WS-FOUND", "X", value="'N'", horror=H28),
    ],
    "linkage": [I(1, "LK-REQUEST", horror=H28, kids=[I(5, "LK-CODE", "X(4)"), I(5, "LK-RATE", "9V9(4)")])],
    "using": ["LK-REQUEST"],
    "units": [
        para("MAIN-PARA",
             raw("MOVE LK-CODE TO VB-CODE"),
             perform("LOOKUP-RATE"),
             if_("WS-FOUND = 'Y'", [raw("MOVE VB-RATE TO LK-RATE")]),
             goback()),
        # a 6-character word and a hyphen: `LOOKUP-RATE.` puts `-` where a fixed-format
        # line has its indicator area (column 7)
        para("LOOKUP-RATE", raw("MOVE 0.0500 TO VB-RATE", "MOVE 'Y' TO WS-FOUND"), horror=H28),
    ],
}

APP = {
    "id": "MODN",
    "title": "Modernised rate service (free format)",
    "style": "free-format COBOL",
    "programs": [MODRATE],
}
