"""HKEP -- the Hierarchy Keep, the fourth Open World level estate (gitgalaxy#7065, #4893 IMS).
A batch shop that walks an IMS database through DL/I calls from COBOL. The program CALLs CBLTDLI with a
function code, a PCB, an I/O area and (here) no SSA, and the database is described by a DBD written as
HLASM macro statements. Every name and layout here is original to this estate.

Slice 1, only what an IBM quote was verified for: H-0096 (DBDGEN: SEGM statements in hierarchic order),
H-0097 (an unqualified GN repeated until the GB status code), H-0098 (a GN issued again after GB).
Slice 2 (a quote read from the IMS 15.1 manual for each): H-0114 (PSBGEN with a database PCB and SENSEGs),
H-0115 (DBD FIELD after its SEGM), H-0116 (DBD LCHILD after its SEGM/FIELD), H-0117 (a qualified SSA).
EXEC DLI, GU/ISRT/REPL/DLET beyond the one GU here, and the DFSRRC00 step are later slices."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H96, H97, H98 = "H-0096", "H-0097", "H-0098"
H114, H115, H116, H117 = "H-0114", "H-0115", "H-0116", "H-0117"

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

# ---- slice 2: DBD FIELD / LCHILD (H-0115, H-0116), PSBGEN with SENSEG (H-0114), a qualified SSA (H-0117)


def _field(name, seg, start=1, nbytes=8):
    return {"op": "FIELD", "operands": [f"NAME=({name},SEQ,U)", f"BYTES={nbytes}", f"START={start}", "TYPE=C"],
            "facts": [{"channel": "ims_gen", "kind": "FIELD", "name": name, "segment": seg, "bytes": nbytes,
                       "start": start}]}


HKEPDB2 = {
    "member": "HKEPDB2", "csect": "", "numbered": False, "horror": H115, **ERA,
    "comments": ["HKEPDB2 - KEEP DATABASE WITH SEQUENCE FIELDS AND A LOGICAL CHILD"],
    "statements": [
        {"op": "DBD", "operands": ["NAME=HKEPDB2,ACCESS=(HDAM,VSAM)"],
         "facts": [{"channel": "ims_gen", "kind": "DBD", "name": "HKEPDB2"}]},
        _seg("KEEP", None, ""),
        _field("KEEPKEY", "KEEP"),
        {"op": "LCHILD", "operands": ["NAME=(ENTRY,HKEPDB3)"], "horror": H116,
         "facts": [{"channel": "ims_gen", "kind": "LCHILD", "name": "ENTRY", "dbname": "HKEPDB3",
                    "segment": "KEEP"}]},
        _seg("WALL", "KEEP", ""),
        _field("WALLKEY", "WALL"),
        {"op": "DBDGEN", "operands": []},
        {"op": "FINISH", "operands": []},
    ],
}


def _senseg(name, parent):
    return {"op": "SENSEG", "operands": [f"NAME={name}"] + ([f"PARENT={parent}"] if parent else []),
            "facts": [{"channel": "ims_gen", "kind": "SENSEG", "name": name, "pcb": "HKEPDB2"}]}


HKEPPSB = {
    "member": "HKEPPSB", "csect": "", "numbered": False, "horror": H114, **ERA,
    "comments": ["HKEPPSB - PSB FOR HKEPFIND: DB PCB SENSITIVE TO KEEP AND WALL"],
    "statements": [
        {"op": "PCB", "operands": ["TYPE=DB", "DBDNAME=HKEPDB2", "PROCOPT=G", "KEYLEN=16"],
         "facts": [{"channel": "ims_gen", "kind": "PCB", "name": "HKEPDB2"}]},
        _senseg("KEEP", None),
        _senseg("WALL", "KEEP"),
        {"op": "PSBGEN", "operands": ["PSBNAME=HKEPPSB", "LANG=COBOL"],
         "facts": [{"channel": "ims_gen", "kind": "PSB", "name": "HKEPPSB"}]},
    ],
}

HKEPFIND = {
    "member": "HKEPFIND", **ERA,
    "program_id": "HKEPFIND", "author": AUTHOR,
    "remarks": ["HKEPFIND - GET ONE KEEP BY KEY WITH A QUALIFIED SSA."],
    "ws": [
        I(1, "WS-GU", "X(4)", value="'GU  '"),
        I(1, "WS-IO-AREA", "X(80)"),
        I(1, "SSA-KEEP", kids=[
            I(5, "SSA-SEGNAME", "X(8)", value="'KEEP    '", horror=H117),
            I(5, "SSA-LPAREN", "X", value="'('", horror=H117),
            I(5, "SSA-FLDNAME", "X(8)", value="'KEEPKEY '", horror=H117),
            I(5, "SSA-OPER", "XX", value="' ='", horror=H117),
            I(5, "SSA-FLDVAL", "X(8)", value="'K0001234'", horror=H117),
            I(5, "SSA-RPAREN", "X", value="')'", horror=H117),
        ]),
    ],
    "linkage": [
        I(1, "IO-PCB", kids=[I(5, "IO-LTERM", "X(8)"), I(5, "IO-RSV", "X(2)"), I(5, "IO-STATUS", "X(2)")]),
        I(1, "DB-PCB", kids=[I(5, "DB-DBD", "X(8)"), I(5, "DB-LEVEL", "X(2)"), I(5, "DB-STATUS", "X(2)")]),
    ],
    "using": ["IO-PCB", "DB-PCB"],
    "units": [
        para("0000-MAIN",
             call("CBLTDLI", using=["WS-GU", "DB-PCB", "WS-IO-AREA", "SSA-KEEP"], horror=H117),
             if_("DB-STATUS = SPACES", [raw("DISPLAY 'KEEP FOUND'")]),
             goback()),
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
    "programs": [HKEPWALK, HKEPFIND],
    "jcl": [],
    "procs": [],
    "macro_tables": [HKEPDBD, HKEPDB2, HKEPPSB],
}
