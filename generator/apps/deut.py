"""DEUT -- a German savings bank's interest calculation, DECIMAL-POINT IS COMMA. Members in
EBCDIC cp273: the program with NEL line ends (z/OS UNIX), the rate copybook as 80-byte records.

Planted: H-0036 (raw EBCDIC NEL), H-0043 (DECIMAL-POINT IS COMMA, VALUE 1,50 in a copybook,
#3942)."""

from ..data import I
from ..stmt import goback, para, raw

H36, H43 = "H-0036", "H-0043"

COPYBOOKS = [
    # the copybook has no SPECIAL-NAMES of its own: its 1,50 is a decimal comma only because
    # the program that copies it declares DECIMAL-POINT IS COMMA (#3942)
    {"member": "ZINSSATZ", "header": [" ZINSSATZ - ZINSSAETZE (KOMMA ALS DEZIMALZEICHEN)"], "horror": H43,
     "encoding": ("cp273", "fb80"),
     "items": [I(5, "ZINS-SATZ", "9V99", value="1,50"), I(5, "GEBÜHR", "9(3)V99", value="12,50")]},
]

ZINSBER = {
    "member": "ZINSBER",
    "program_id": "ZINSBER",
    "member_horror": H36,
    "author": "SPARKASSE",
    "remarks": ["ZINSBER - ZINSEN FUER DAS LAUFENDE JAHR."],
    "special_names": ["DECIMAL-POINT IS COMMA"],
    "special_names_horror": H43,
    "ws": [
        I(1, "WS-ZINS", copy=["ZINSSATZ"], horror=H43),
        I(1, "BETRÄGE", horror=H43, kids=[
            I(5, "BETRAG", "9(7)V99", value="1000,00"),
            I(5, "ERGEBNIS", "ZZZ.ZZ9,99"),
            I(5, "TABELLE", occurs=3, kids=[I(10, "T-WERT", "9V9")]),
        ]),
        # an entry with a USAGE of its own last: #4329 must not touch the horror's items
        I(1, "WS-ENDE", "S9(4)", "COMP"),
    ],
    "units": [
        para("0000-START",
             raw("COMPUTE BETRAG = BETRAG * ZINS-SATZ", "MOVE 0,5 TO T-WERT (2)",
                 "MOVE BETRAG TO ERGEBNIS", "DISPLAY ERGEBNIS"),
             goback(),
             horror=H43),
    ],
}

APP = {
    "id": "DEUT",
    "title": "German interest calculation (EBCDIC cp273, decimal comma)",
    "style": "raw EBCDIC cp273: program NEL, copybook FB80; DECIMAL-POINT IS COMMA",
    "encodings": {"cobol": ("cp273", "nel"), "copybook": ("cp273", "fb80")},
    "copybooks": COPYBOOKS,
    "programs": [ZINSBER],
}
