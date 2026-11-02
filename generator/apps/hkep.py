"""HKEP -- the Hierarchy Keep, the fourth Open World level estate (gitgalaxy#7065, #4893 IMS).
A batch shop that walks an IMS database through DL/I calls from COBOL. The program CALLs CBLTDLI with a
function code, a PCB, an I/O area and (here) no SSA, and the database is described by a DBD written as
HLASM macro statements. Every name and layout here is original to this estate.

Slice 1, only what an IBM quote was verified for: H-0096 (DBDGEN: SEGM statements in hierarchic order),
H-0097 (an unqualified GN repeated until the GB status code), H-0098 (a GN issued again after GB).
PSBGEN, SENSEG, FIELD, LCHILD, EXEC DLI and the DFSRRC00 step are later slices (no verified quote yet)."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H96, H97, H98 = "H-0096", "H-0097", "H-0098"

AUTHOR = "KEEP SYSTEMS"
ERA = {"era": 2, "era_evidence": "END-IF (COBOL-85); DL/I is a static CALL interface to CBLTDLI"}

HKEPWALK = {
    "member": "HKEPWALK", **ERA,
    "program_id": "HKEPWALK", "author": AUTHOR,
    "remarks": ["HKEPWALK - WALK THE KEEP DATABASE WITH UNQUALIFIED GN CALLS.",
                "THE LOOP ENDS ON STATUS GB; ONE MORE GN RESTARTS THE WALK."],
    "ws": [
        I(1, "WS-GN", "X(4)", value="'GN  '"),
        I(1, "WS-COUNT", "S9(4)", "COMP", value="0"),
        I(1, "WS-IO-AREA", "X(80)"),
    ],
    "linkage": [
        I(1, "IO-PCB", kids=[I(5, "IO-LTERM", "X(8)"), I(5, "IO-RSV", "X(2)"), I(5, "IO-STATUS", "X(2)")]),
        I(1, "DB-PCB", kids=[I(5, "DB-DBD", "X(8)"), I(5, "DB-LEVEL", "X(2)"), I(5, "DB-STATUS", "X(2)")]),
    ],
    "using": ["IO-PCB", "DB-PCB"],
    "units": [
        para("0000-MAIN",
             perform("1000-SCAN"),
             perform("2000-RESTART"),
             goback()),
        para("1000-SCAN",
             call("CBLTDLI", using=["WS-GN", "DB-PCB", "WS-IO-AREA"], horror=H97),
             if_("DB-STATUS = SPACES",
                 [raw("ADD 1 TO WS-COUNT"), perform("1000-SCAN")])),
        para("2000-RESTART",
             call("CBLTDLI", using=["WS-GN", "DB-PCB", "WS-IO-AREA"], horror=H98),
             if_("DB-STATUS = SPACES", [raw("DISPLAY 'RESTARTED AT FIRST ROOT'")])),
    ],
}


def _seg(name, parent, line_remark):
    ops = f"NAME={name},BYTES=40" + (f",PARENT={parent}" if parent else "")
    return {"op": "SEGM", "operands": [ops], "remark": line_remark,
            "facts": [{"channel": "ims_gen", "kind": "SEGM", "name": name, "parent": parent or "", "bytes": 40}]}


HKEPDBD = {
    "member": "HKEPDBD", "csect": "", "numbered": False, "horror": H96, **ERA,
    "comments": ["HKEPDBD - KEEP DATABASE: ROOT KEEP, DEPENDENTS WALL, GATE"],
    "statements": [
        {"op": "DBD", "operands": ["NAME=HKEPDB,ACCESS=(HDAM,VSAM)"],
         "facts": [{"channel": "ims_gen", "kind": "DBD", "name": "HKEPDB"}]},
        _seg("KEEP", None, ""),
        _seg("WALL", "KEEP", ""),
        _seg("GATE", "WALL", ""),
        {"op": "DBDGEN", "operands": []},
        {"op": "FINISH", "operands": []},
    ],
}

APP = {
    "id": "HKEP",
    "era": 2,
    "era_evidence": "END-IF (COBOL-85); static CALL to CBLTDLI and HLASM DBD macros",
    "title": "Hierarchy Keep (batch IMS: DL/I calls and a DBD)",
    "style": "batch COBOL over DL/I (CBLTDLI) with a DBDGEN member",
    "copybooks": [],
    "dclgen": [],
    "programs": [HKEPWALK],
    "jcl": [],
    "procs": [],
    "macro_tables": [HKEPDBD],
}
