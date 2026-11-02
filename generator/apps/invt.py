"""INVT -- inventory stock status, written in 1983. The estate's era-1 app: a card-deck batch
program (sequence numbers in cols 1-6, the deck name in 73-80, upper case throughout) built from
SECTIONs, period-terminated sentences, with no COBOL-85 construct. One program, one
record copybook, one job.

Planted: H-0061 (CICS BLL cells in INVTONL), H-0062 (SERVICE RELOAD in INVTRLD), H-0099 (a record over 4096 bytes
addressed by a secondary BLL cell in INVTLRG), gitgalaxy#5118, #5119."""

from ..data import I
from ..stmt import cics, goback, if_, para, perform, raw, section

H61 = "H-0061"
H62 = "H-0062"
H63 = "H-0099"

COPYBOOKS = [
    {"member": "INVTREC", "numbered": True, "header": [" INVTREC  - INVENTORY STOCK RECORD (80 BYTES)"],
     "items": [
         I(5, "STK-PART-NO", "X(10)"),
         I(5, "STK-DESC", "X(30)"),
         I(5, "STK-ON-HAND", "S9(7)", "COMP-3"),
         I(5, "STK-REORDER-PT", "S9(7)", "COMP-3"),
         I(5, "STK-BIN", "X(6)"),
         I(5, "FILLER", "X(26)"),
     ]},
]

INVTBAT = {
    "member": "INVTBAT",
    "era": 1,
    "era_evidence": "SECTIONs and period-terminated sentences only; no END-IF, END-READ or inline PERFORM, so OS/VS COBOL (#5117 era 1)",
    "program_id": "INVTBAT",
    "numbered": True,
    "ident": "INVTBAT",
    "banner": [
        "*****************************************************************",
        "*   INVTBAT  -  STOCK STATUS REPORT, REORDER POINT CHECK        *",
        "*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 06/14/83     *",
        "*****************************************************************",
        "/",
    ],
    "author": "D KOWALCZYK",
    "installation": "MATERIALS CONTROL",
    "date_written": "06/14/83",
    "remarks": ["INVTBAT - LIST STOCK AT OR BELOW REORDER POINT."],
    "selects": [{"name": "STOCK-FILE", "assign": "STOCKIN", "status": "WS-STOCK-STATUS"},
                {"name": "LIST-FILE", "assign": "STKLIST", "status": "WS-LIST-STATUS"}],
    "fds": [{"fd": "STOCK-FILE", "record": I(1, "STOCK-IN", "X(80)")},
            {"fd": "LIST-FILE", "record": I(1, "LIST-LINE", "X(133)")}],
    "ws": [
        I(1, "WS-STOCK-STATUS", "X(2)"),
        I(1, "WS-LIST-STATUS", "X(2)"),
        I(1, "WS-EOF", "X", value="'N'"),
        I(1, "WS-LOW-COUNT", "9(5)", "COMP-3", value="0"),
        I(1, "WS-REC", copy=["INVTREC"]),
    ],
    "units": [
        section("0000-MAINLINE",
                raw("OPEN INPUT STOCK-FILE OUTPUT LIST-FILE"),
                perform("1000-PROCESS-STOCK", until="WS-EOF = 'Y'"),
                raw("CLOSE STOCK-FILE LIST-FILE"),
                goback()),
        section("1000-PROCESS-STOCK",
                perform("1100-READ-STOCK"),
                if_("WS-EOF NOT = 'Y'", [perform("1200-CHECK-REORDER")], end_if=False)),
        section("1100-READ-STOCK",
                raw("READ STOCK-FILE INTO WS-REC AT END MOVE 'Y' TO WS-EOF")),
        section("1200-CHECK-REORDER",
                if_("STK-ON-HAND NOT > STK-REORDER-PT",
                    [raw("ADD 1 TO WS-LOW-COUNT", "MOVE SPACES TO LIST-LINE", "MOVE STK-PART-NO TO LIST-LINE",
                         "WRITE LIST-LINE")], end_if=False)),
    ],
}

INVTONL = {
    "member": "INVTONL",
    "era": 1,
    "era_evidence": "command-level EXEC CICS with BLL cells (S9(8) COMP LINKAGE cells filled by ADDRESS and READ SET) and no RESP, HANDLE or ADDRESS OF: CICS/VS 1.x command level, #5117 era 1",
    "program_id": "INVTONL",
    "numbered": True,
    "ident": "INVTONL",
    "banner": [
        "*****************************************************************",
        "*   INVTONL  -  ONLINE STOCK INQUIRY (TRANSACTION INVQ)         *",
        "*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 09/22/83     *",
        "*****************************************************************",
        "/",
    ],
    "author": "D KOWALCZYK",
    "installation": "MATERIALS CONTROL",
    "date_written": "09/22/83",
    "remarks": ["INVTONL - STOCK INQUIRY, RECORD ADDRESSED BY BLL CELL."],
    "compile": "compiled-stubbed",
    "procedure_header_horror": H61,
    "ws": [
        I(1, "WS-PART-KEY", "X(10)"),
    ],
    "linkage": [
        I(1, "BLL-CELLS", horror=H61, kids=[
            I(2, "FILLER", "S9(8)", "COMP", horror=H61),
            I(2, "STK-BLL", "S9(8)", "COMP", horror=H61),
            I(2, "CWA-BLL", "S9(8)", "COMP", horror=H61),
        ]),
        I(1, "STK-AREA", copy=["INVTREC"]),
        I(1, "CWA-AREA", kids=[I(2, "CWA-PART-KEY", "X(10)"), I(2, "FILLER", "X(70)")], horror=H61),
    ],
    "units": [
        section("0000-MAINLINE",
                cics("ADDRESS CWA(CWA-BLL)", horror=H61),
                raw("MOVE CWA-PART-KEY TO WS-PART-KEY"),
                cics("READ DATASET('INVTMST') SET(STK-BLL)", "RIDFLD(WS-PART-KEY)",
                     resource={"verb": "READ", "kind": "FILE", "name": "INVTMST", "record": "STK-AREA",
                               "access": "read"},
                     horror=H61),
                cics("RETURN")),
    ],
}

INVTRLD = {
    "member": "INVTRLD",
    "era": 1,
    "era_evidence": "SERVICE RELOAD after each BLL cell change, an OS/VS COBOL compiler control statement that later compilers ignore (CICS Application Programming Guide, Appendix B): OS/VS COBOL, #5117 era 1",
    "program_id": "INVTRLD",
    "numbered": True,
    "ident": "INVTRLD",
    "banner": [
        "*****************************************************************",
        "*   INVTRLD  -  ONLINE STOCK BROWSE, SERVICE RELOAD AFTER BLL   *",
        "*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 11/08/83     *",
        "*****************************************************************",
        "/",
    ],
    "author": "D KOWALCZYK",
    "installation": "MATERIALS CONTROL",
    "date_written": "11/08/83",
    "remarks": ["INVTRLD - STOCK RECORD BY BLL CELL, RELOADED."],
    "compile": "ibm-only",
    "compile_reason": "SERVICE RELOAD is an OS/VS COBOL compiler control statement; GnuCOBOL -std=ibm rejects it",
    "compile_check": ("service-reload", "every SERVICE RELOAD statement becomes CONTINUE (padded to the same width) for the check; the rest compiles as written"),
    "phantoms": [
        {"channel": "data_moves", "verb": "SERVICE", "target": t, "horror": H62,
         "why": "SERVICE RELOAD is a compiler control statement that moves no data; its operand is a LINKAGE area, not a move target"}
        for t in ("PARMLIST", "STK-AREA")],
    "ws": [
        I(1, "WS-PART-KEY", "X(10)"),
        I(1, "WS-BUMP", "S9(8)", "COMP", value="4096"),
    ],
    "linkage": [
        I(1, "PARMLIST", kids=[I(2, "PARM-BLL", "S9(8)", "COMP")]),
        I(1, "BLL-CELLS", kids=[
            I(2, "FILLER", "S9(8)", "COMP"),
            I(2, "STK-BLL", "S9(8)", "COMP"),
        ]),
        I(1, "STK-AREA", copy=["INVTREC"]),
    ],
    "units": [
        section("0000-MAINLINE",
                raw("SERVICE RELOAD PARMLIST", horror=H62),
                raw("MOVE SPACES TO WS-PART-KEY"),
                cics("READ DATASET('INVTMST') SET(STK-BLL)", "RIDFLD(WS-PART-KEY)",
                     resource={"verb": "READ", "kind": "FILE", "name": "INVTMST", "record": "STK-AREA",
                               "access": "read"}),
                raw("ADD WS-BUMP TO STK-BLL"),
                raw("SERVICE RELOAD STK-AREA", horror=H62),
                cics("RETURN")),
    ],
}

INVTLRG = {
    "member": "INVTLRG",
    "era": 1,
    "era_evidence": "a LINKAGE record over 4096 bytes addressed by a second BLL cell set with ADD 4096 and then SERVICE RELOAD (CICS Application Programming Guide, Appendix B, 'BLL and large storage areas'): OS/VS COBOL, #5117 era 1",
    "program_id": "INVTLRG",
    "numbered": True,
    "ident": "INVTLRG",
    "banner": [
        "*****************************************************************",
        "*   INVTLRG  -  ONLINE STOCK DETAIL, LONG RECORD BY BLL CELLS   *",
        "*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 02/21/84     *",
        "*****************************************************************",
        "/",
    ],
    "author": "D KOWALCZYK",
    "installation": "MATERIALS CONTROL",
    "date_written": "02/21/84",
    "remarks": ["INVTLRG - 5400 BYTE DETAIL RECORD, TWO BLL CELLS."],
    "compile": "ibm-only",
    "compile_reason": "SERVICE RELOAD is an OS/VS COBOL compiler control statement; GnuCOBOL -std=ibm rejects it",
    "compile_check": ("service-reload", "every SERVICE RELOAD statement becomes CONTINUE (padded to the same width) for the check; the rest compiles as written"),
    "phantoms": [
        {"channel": "data_moves", "verb": "SERVICE", "target": t, "horror": H63,
         "why": "SERVICE RELOAD is a compiler control statement that moves no data; its operand is a LINKAGE area, not a move target"}
        for t in ("STK-LONG", "STK-FULL")],
    "ws": [
        I(1, "WS-PART-KEY", "X(10)"),
    ],
    "linkage": [
        I(1, "BLL-CELLS", horror=H63, kids=[
            I(2, "FILLER", "S9(8)", "COMP", horror=H63),
            I(2, "LONG-BLL", "S9(8)", "COMP", horror=H63),
            I(2, "LONG-BLL2", "S9(8)", "COMP", horror=H63),
            I(2, "FULL-BLL", "S9(8)", "COMP", horror=H63),
        ]),
        I(1, "STK-LONG", horror=H63, kids=[
            I(2, "LNG-HEADER", "X(4000)", horror=H63),
            I(2, "LNG-DETAIL", "X(1000)", horror=H63),
            I(2, "LNG-TRAILER", "X(400)", horror=H63),
        ]),
        I(1, "STK-FULL", horror=H63, kids=[
            I(2, "FUL-BODY", "X(4096)", horror=H63),
        ]),
    ],
    "units": [
        section("0000-MAINLINE",
                raw("MOVE SPACES TO WS-PART-KEY"),
                cics("READ DATASET('INVTDTL') SET(LONG-BLL)", "RIDFLD(WS-PART-KEY)",
                     resource={"verb": "READ", "kind": "FILE", "name": "INVTDTL", "record": "STK-LONG",
                               "access": "read"},
                     horror=H63),
                raw("ADD 4096 LONG-BLL GIVING LONG-BLL2", horror=H63),
                raw("SERVICE RELOAD STK-LONG", horror=H63),
                cics("READ DATASET('INVTFUL') SET(FULL-BLL)", "RIDFLD(WS-PART-KEY)",
                     resource={"verb": "READ", "kind": "FILE", "name": "INVTFUL", "record": "STK-FULL",
                               "access": "read"},
                     horror=H63),
                raw("SERVICE RELOAD STK-FULL", horror=H63),
                cics("RETURN")),
    ],
}

JOBS = [
    {
        "name": "INVTDLY",
        "title": "INVT STOCK STATUS",
        "accounting": "(INVT,0683)",
        "notify": False,
        "comments": ["NIGHTLY STOCK STATUS AND REORDER POINT LIST"],
        "steps": [
            {"name": "STEP010", "pgm": "INVTBAT", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.INVT.LOADLIB", "disp": ("SHR",)},
                {"name": "STOCKIN", "dsn": "PROD.INVT.STOCK", "disp": ("SHR",)},
                {"name": "STKLIST", "sysout": "A"},
                {"name": "SYSOUT", "sysout": "*"},
            ]},
        ],
    },
]

APP = {
    "id": "INVT",
    "era": 1,
    "era_evidence": "INVTBAT and INVTONL have no construct later than OS/VS COBOL and CICS/VS command level; a 1983 card-deck system",
    "title": "Inventory stock status (1983 batch deck)",
    "style": "1980s card deck: numbered cols 1-6, deck name in cols 73-80, upper case, SECTIONs, period-terminated IF",
    "copybooks": COPYBOOKS,
    "programs": [INVTBAT, INVTONL, INVTRLD, INVTLRG],
    "jcl": JOBS,
}
