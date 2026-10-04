"""CUST -- customer inquiry, online. CICS pseudo-conversational programs over a BMS map and a
Db2 access module. Unnumbered members (edited in a modern IDE, cols 1-6 blank).

Planted: H-0002 (conditional CICS RETURN, a RETURN-named paragraph and EXIT PERFORM in an
unnumbered member, CUSTINQ),
H-0005 (EXEC SQL CALL of stored procedures, CUSTDBIO)."""

from ..data import SQLINC, C, I
from ..stmt import cics, exit_perform, if_, para, perform, perform_inline, raw, sql

H2 = "H-0002"
H5 = "H-0005"

COPYBOOKS = [
    {
        "member": "CUSTCOMM",
        "header": [" CUSTCOMM - CUSTOMER INQUIRY COMMAREA (50 BYTES)"],
        "items": [
            I(5, "CA-CUST-ID", "X(8)"),
            I(5, "CA-RETURN-CODE", "S9(4)", "COMP"),
            I(5, "CA-MSG", "X(40)"),
        ],
    },
]

BMS = [
    {
        "mapset": "CUSTMS",
        "maps": [
            {"name": "CUSTMAP", "size": (24, 80), "fields": [
                {"pos": (1, 30), "length": 16, "attrb": "ASKIP,BRT", "initial": "CUSTOMER INQUIRY"},
                {"pos": (4, 5), "length": 12, "attrb": "ASKIP,NORM", "initial": "CUSTOMER ID:"},
                {"name": "CUSTID", "pos": (4, 20), "length": 8, "attrb": "UNPROT,IC,FSET", "picin": "X(8)"},
                {"pos": (6, 5), "length": 12, "attrb": "ASKIP,NORM", "initial": "NAME       :"},
                {"name": "CUSTNM", "pos": (6, 20), "length": 30, "attrb": "ASKIP,NORM"},
                {"pos": (7, 5), "length": 12, "attrb": "ASKIP,NORM", "initial": "BALANCE    :"},
                {"name": "CUSTBAL", "pos": (7, 20), "length": 15, "attrb": "ASKIP,NORM"},
                {"name": "MSG", "pos": (23, 1), "length": 79, "attrb": "ASKIP,BRT"},
            ]},
        ],
    },
]

DCLGEN = [
    {
        "member": "DCLCUST",
        "table": "PROD.CUSTOMER",
        "library": "PROD.CUST.DCLGEN(DCLCUST)",
        "structure": "DCLCUSTOMER",
        "columns": [
            ("CUST_ID", "CHAR", 8, None, False),
            ("CUST_NAME", "VARCHAR", 30, None, False),
            ("CUST_BAL", "DECIMAL", 11, 2, True),
            ("CUST_UPD_DATE", "DATE", None, None, True),
        ],
    },
]

CUSTINQ = {
    "member": "CUSTINQ",
    "program_id": "CUSTINQ",
    "author": "CUSTOMER SYSTEMS",
    "remarks": [
        "CUSTINQ - CUSTOMER INQUIRY (TRANSACTION CINQ).",
        "PSEUDO-CONVERSATIONAL.",
        "FIRST ENTRY (EIBCALEN = 0) SENDS THE EMPTY MAP AND RETURNS.",
    ],
    "compile": "compiled-stubbed",
    "ws": [
        I(1, "WS-COMMAREA", copy=["CUSTCOMM"]),
        C("CUSTMS"),
        C("DFHAID"),
        I(1, "WS-RESP", "S9(8)", "COMP"),
        I(1, "WS-DATE-AREA", copy=["DATEWS"]),
        I(1, "WS-I", "S9(4)", "COMP"),
    ],
    "linkage": [I(1, "DFHCOMMAREA", "X(50)")],
    "units": [
        para("0000-MAIN",
             if_("EIBCALEN = 0", [
                 raw("MOVE LOW-VALUES TO CUSTMAPO"),
                 cics("SEND MAP('CUSTMAP') MAPSET('CUSTMS') ERASE"),
                 cics("RETURN TRANSID('CINQ')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="CINQ",
                      own_line=True),
             ]),
             raw("MOVE DFHCOMMAREA TO WS-COMMAREA"),
             perform("1000-RECEIVE-MAP"),
             if_("EIBAID = DFHPF3", [perform("RETURN-TO-MENU")]),
             perform("2000-LOOKUP-CUSTOMER"),
             perform("3000-SEND-MAP"),
             perform("4000-FIND-BLANK"),
             cics("RETURN TRANSID('CINQ')", "COMMAREA(WS-COMMAREA)", verb="RETURN TRANSID", operand="CINQ"),
             horror=H2),
        para("1000-RECEIVE-MAP",
             cics("RECEIVE MAP('CUSTMAP') MAPSET('CUSTMS')", "INTO(CUSTMAPI) RESP(WS-RESP)"),
             raw("MOVE CUSTIDI TO CA-CUST-ID")),
        para("RETURN-TO-MENU",
             raw("MOVE 'RETURNING TO MENU' TO CA-MSG"),
             perform("9100-SAVE-STATE"),
             cics("XCTL PROGRAM('CUSTMNU')", "COMMAREA(WS-COMMAREA)", verb="XCTL", operand="CUSTMNU"),
             horror=H2),
        para("2000-LOOKUP-CUSTOMER",
             cics("LINK PROGRAM('CUSTDBIO')", "COMMAREA(WS-COMMAREA)", verb="LINK", operand="CUSTDBIO"),
             if_("CA-RETURN-CODE NOT = 0", [raw("MOVE CA-MSG TO MSGO")])),
        para("3000-SEND-MAP",
             raw("MOVE CA-CUST-ID TO CUSTIDO"),
             cics("SEND MAP('CUSTMAP') MAPSET('CUSTMS')", "DATAONLY CURSOR")),
        para("4000-FIND-BLANK",
             perform_inline("VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 8", [
                 if_("CA-CUST-ID (WS-I:1) = SPACE", [exit_perform(horror="H-0006")]),
             ]),
             perform("9100-SAVE-STATE"),
             horror=H2),
        para("9100-SAVE-STATE",
             raw("MOVE SPACES TO CA-CUST-ID")),
    ],
}

CUSTDBIO = {
    "member": "CUSTDBIO",
    "program_id": "CUSTDBIO",
    "author": "CUSTOMER SYSTEMS",
    "remarks": [
        "CUSTDBIO - CUSTOMER DB2 ACCESS. LINKED FROM CUSTINQ.",
        "BALANCE REFRESH AND AUDIT ARE DB2 STORED PROCEDURES.",
    ],
    "compile": "compiled-stubbed",
    "ws": [
        SQLINC("SQLCA"),
        SQLINC("DCLCUST"),
        I(1, "WS-SQLCODE", "-9(9)"),
        I(1, "WS-BAL-IND", "S9(4)", "COMP"),
    ],
    "linkage": [I(1, "DFHCOMMAREA", copy=["CUSTCOMM"])],
    "units": [
        para("0000-MAIN",
             raw("MOVE CA-CUST-ID TO CUST-ID"),
             perform("1000-SELECT-CUSTOMER"),
             if_("SQLCODE = 0", [perform("2000-REFRESH-BALANCE")]),
             cics("RETURN")),
        para("1000-SELECT-CUSTOMER",
             sql("SELECT CUST_NAME, CUST_BAL",
                 "  INTO :CUST-NAME, :CUST-BAL :WS-BAL-IND",
                 "  FROM PROD.CUSTOMER",
                 " WHERE CUST_ID = :CUST-ID",
                 verb="SELECT", table="PROD.CUSTOMER", access="read"),
             if_("SQLCODE NOT = 0", [raw("MOVE SQLCODE TO WS-SQLCODE", "MOVE 8 TO CA-RETURN-CODE")])),
        para("2000-REFRESH-BALANCE",
             sql("CALL PRODPROC.CUSTBAL", "     (:CUST-ID, :CUST-BAL)", verb="CALL", proc="PRODPROC.CUSTBAL",
                 horror=H5),
             sql("CALL CUSTAUDT", verb="CALL", proc="CUSTAUDT", horror=H5),
             sql("UPDATE PROD.CUSTOMER",
                 "   SET CUST_UPD_DATE = CURRENT DATE",
                 " WHERE CUST_ID = :CUST-ID",
                 verb="UPDATE", table="PROD.CUSTOMER", access="update")),
    ],
}

CUSTMNU = {
    "member": "CUSTMNU",
    "program_id": "CUSTMNU",
    "author": "CUSTOMER SYSTEMS",
    "remarks": ["CUSTMNU - CUSTOMER SYSTEMS MENU (TRANSACTION CMNU)."],
    "compile": "compiled-stubbed",
    "ws": [I(1, "WS-MENU-TEXT", "X(40)", value="'CUSTOMER SYSTEMS: CINQ = INQUIRY'")],
    "units": [
        para("0000-MAIN",
             cics("SEND TEXT FROM(WS-MENU-TEXT) ERASE"),
             cics("RETURN TRANSID('CMNU')", verb="RETURN TRANSID", operand="CMNU")),
    ],
}

CSD = [
    {
        "group": "CUSTGRP",
        "title": "CUSTOMER INQUIRY",
        "defines": [
            ("PROGRAM", "CUSTINQ", {"LANGUAGE": "COBOL"}),
            ("PROGRAM", "CUSTDBIO", {"LANGUAGE": "COBOL"}),
            ("PROGRAM", "CUSTMNU", {"LANGUAGE": "COBOL"}),
            ("MAPSET", "CUSTMS", {}),
            ("TRANSACTION", "CINQ", {"PROGRAM": "CUSTINQ"}),
            ("TRANSACTION", "CMNU", {"PROGRAM": "CUSTMNU"}),
        ],
    },
]

APP = {
    "id": "CUST",
    "title": "Customer inquiry (CICS, Db2)",
    "style": "unnumbered fixed format, pseudo-conversational CICS, Db2 stored procedures",
    "copybooks": COPYBOOKS,
    "bms": BMS,
    "dclgen": DCLGEN,
    "programs": [CUSTINQ, CUSTDBIO, CUSTMNU],
    "csd": CSD,
}
