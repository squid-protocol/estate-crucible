"""NORD -- a Danish bank's interest run. Programs are PDS members transferred in binary: raw
EBCDIC cp277, 80-byte records, no line ends. Copybooks kept their z/OS UNIX form (cp277,
NEL line ends). The job was transferred as text (UTF-8). Names use the Danish letters Æ Ø Å,
which cp277 puts where cp037 has @ # $.

Enterprise COBOL words allow only A-Z, 0-9, - and _: the COBOL side names its Nordic
members through literals (PROGRAM-ID 'KØBREG', COPY 'KUNDEÅ'); PL/I (extralingual
characters) and JCL (national characters) use Æ Ø Å in their own names.

Planted: H-0035 (raw EBCDIC FB80), H-0037 (D016 stray NUL bytes), H-0039 (D015 Nordic
names in COBOL, PL/I and JCL), H-0044 (EBCDIC collation), H-0047 (D013), H-0048 (D023),
H-0049 (D039)."""

from ..data import CP, I
from ..pli import pcall, praw
from ..stmt import goback, if_, para, perform, raw

H35, H37, H39, H44, H47, H48, H49 = "H-0035", "H-0037", "H-0039", "H-0044", "H-0047", "H-0048", "H-0049"

COPYBOOKS = [
    {"member": "KUNDEÅ", "header": [" KUNDEÅ   - KUNDEPOST (KUNDE-NR, NAVN, BELØB)"], "horror": H39,
     "items": [I(5, "KUNDE-NR", "X(8)"), I(5, "KUNDE-NAVN", "X(30)"), I(5, "BELOEB", "S9(9)V99", "COMP-3"),
               I(5, "AAR-TIL-DATO", "S9(9)V99", "COMP-3"), I(5, "SAER-KODE", "X")]},
]

KOBREG = {
    "member": "KØBREG",
    "program_id": "KØBREG",
    "program_id_style": "quoted",
    "program_id_horror": H39,
    "member_horror": H35,
    "author": "RENTEAFDELINGEN",
    "remarks": ["KØBREG - BEREGN ÅRETS RENTE PR. KUNDE."],
    "ws": [
        I(1, "KUNDE-DATA", copy=[CP("KUNDEÅ", quoted=True)], horror=H39),
        I(1, "SAERLIG-KODE", "X", value="'A'", horror=H44),
        I(1, "END-OF-FILE", "X", value="'N'", horror=H47),
        I(1, "WS-AAR", "X(4)", horror=H48),
        I(1, "WS-BUF", "X(8)", horror=H49),
        I(1, "RENTE-PCT", "9V99", value="2.50"),
    ],
    "units": [
        para("0000-HOVED",
             perform("BEREGN-RENTE-AAR"),
             if_("SAERLIG-KODE < '0'", [perform("2000-BOGSTAV-FOER-CIFFER")], horror=H44),
             raw("MOVE 'Y' TO END-OF-FILE", horror=H47),
             raw("MOVE FUNCTION CURRENT-DATE (1:4) TO WS-AAR", horror=H48),
             raw("MOVE ALL X'00' TO WS-BUF", horror=H49),
             goback(),
             horror=H35),
        para("BEREGN-RENTE-AAR",
             raw("COMPUTE AAR-TIL-DATO = BELOEB * RENTE-PCT")),
        # IBM's EBCDIC collating sequence puts letters before digits ('A' < '0'); ASCII
        # puts them after. The paragraph runs on z/OS; a port that compares as ASCII skips it.
        para("2000-BOGSTAV-FOER-CIFFER",
             raw("MOVE 'J' TO SAER-KODE"),
             horror=H44),
    ],
}

RENTE = {
    "member": "RENTEØ",
    "proc": "RENTEØ",
    "options": "MAIN",
    "horror": H39,
    "comments": ["RENTEØ - RENTEBEREGNING (PL/I)."],
    "decls": [
        [(1, "SATS_ÅR", "FIXED DEC(5,2)")],
        [(1, "KUNDE_Ø", ""), (2, "KONTO_NR", "CHAR(10)"), (2, "BELØB_ÅR", "FIXED DEC(11,2)")],
    ],
    "stmts": [
        praw("SATS_ÅR = 2;"),
        pcall("NULSTIL_Ø"),
        praw("RETURN;"),
    ],
    "internal": [{"name": "NULSTIL_Ø", "stmts": [praw("BELØB_ÅR = 0;")]}],
}

NULREST = {
    "member": "NULREST",
    "proc": "NULREST",
    "options": "MAIN",
    "horror": H37,
    # two NUL bytes left by a PC transfer at the end of a comment (#3534)
    "comments": ["NULREST - RESTSALDO. OVERFOERT MED FTP (BINAER)." + "\x00\x00"],
    "decls": [[(1, "REST", "FIXED DEC(9,2)")]],
    "stmts": [praw("REST = 0;"), praw("RETURN;")],
}

JOBS = [
    {
        "name": "KØBDAG",
        "title": "DAGLIG RENTE",
        "accounting": "(NORD,0045)",
        "horror": H39,
        "steps": [
            {"name": "RENTE", "pgm": "KØBREG", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.KØB.LOADLIB", "disp": ("SHR",)},
                {"name": "KUNDER", "dsn": "PROD.KØB.KUNDER", "disp": ("SHR",)},
            ]},
        ],
    },
]

APP = {
    "id": "NORD",
    "title": "Danish interest run (EBCDIC cp277)",
    "style": "raw EBCDIC cp277: programs FB80, copybooks NEL; UTF-8 job and PL/I; Æ Ø Å names",
    "encodings": {"cobol": ("cp277", "fb80"), "copybook": ("cp277", "nel")},
    "copybooks": COPYBOOKS,
    "programs": [KOBREG],
    "pli": [RENTE, NULREST],
    "jcl": JOBS,
}
