"""PAYR -- payroll. One source member holds three programs: PAYMAIN, the PAYCALC program
nested in it, and a batch-compiled sibling 'PAYRPT' whose PROGRAM-ID is a literal; each
opens with a MAINLINE SECTION. Copybooks come in every COPY form, and the app's own
DATEWS shadows the shared one.

Planted: H-0016 (D004), H-0022 (D019), H-0029 (D041), H-0031 (D043), H-0033 (PERFORM
UNTIL EXIT), H-0034 (#4265)."""

from ..data import CP, I
from ..stmt import call, exit_perform, goback, if_, para, perform, perform_inline, raw, section

H16, H22, H29, H31, H33, H34 = "H-0016", "H-0022", "H-0029", "H-0031", "H-0033", "H-0034"

COPYBOOKS = [
    {"member": "PAYTPL", "header": [" PAYTPL   - EMPLOYEE TEMPLATE, COPY ... REPLACING ==:TAG:=="],
     "horror": H16,
     "items": [I(5, ":TAG:-ID", "X(6)"), I(5, ":TAG:-NAME", "X(30)"), I(5, ":TAG:-RATE", "S9(5)V99", "COMP-3")]},
    {"member": "PAYCON", "header": [" PAYCON   - PAYROLL CONSTANTS (COPIED BY A QUOTED NAME)"],
     "items": [I(5, "PC-MAX-HOURS", "9(3)", value="168"), I(5, "PC-OT-FACTOR", "9V99", value="1.50")]},
    # the app's own DATEWS: an ISO date, 18 bytes. It shadows shared/copylib DATEWS (16 bytes)
    # for every program of this app that does not name a library (#4265)
    {"member": "DATEWS", "header": [" DATEWS   - PAYROLL'S OWN DATE AREA (ISO, 18 BYTES)"], "horror": H34,
     "items": [I(5, "WS-CURR-DATE", "X(10)"), I(5, "WS-CURR-TIME", "X(8)")]},
]

PAYRPT = {
    "program_id": "PAYRPT",
    "program_id_style": "quoted",
    "program_id_horror": H29,
    "ws": [I(1, "WS-LINES", "9(4)", "COMP", value="0", horror=H31)],
    "units": [
        section("MAINLINE", horror=H31),
        para("0100", raw("ADD 1 TO WS-LINES", "DISPLAY 'PAYRPT ' WS-LINES"), goback(), horror=H31),
    ],
}

PAYCALC = {
    "program_id": "PAYCALC",
    "ws": [I(1, "WS-I", "9(4)", "COMP", value="0", horror=H31),
           I(1, "WS-GROSS", "S9(7)V99", "COMP-3", value="0", horror=H31)],
    "units": [
        section("MAINLINE", horror=H31),
        para("1000-CALC",
             perform_inline("UNTIL EXIT", [
                 raw("ADD 1 TO WS-I"),
                 if_("WS-I > 12", [exit_perform(horror="H-0006")]),
                 raw("ADD 100 TO WS-GROSS"),
             ], horror=H33),
             perform("2000-ROUND"),
             goback(),
             horror=H33),
        para("2000-ROUND", raw("COMPUTE WS-GROSS ROUNDED = WS-GROSS * 1"), horror=H31),
    ],
}

PAYMAIN = {
    "member": "PAYMAIN",
    "program_id": "PAYMAIN",
    "author": "PAYROLL",
    "remarks": [
        "PAYMAIN - PAYROLL RUN. CONTAINS PAYCALC (NESTED); PAYRPT IS",
        "BATCH-COMPILED FROM THE SAME MEMBER.",
    ],
    "member_horror": None,
    "special_names": ["C01 IS TOP-OF-PAGE"],
    "special_names_horror": H22,
    "i_o_control": ["APPLY WRITE-ONLY ON PAY-FILE"],
    "selects": [{"name": "PAY-FILE", "assign": "PAYOUT", "status": "WS-PAY-STATUS"}],
    "fds": [{"fd": "PAY-FILE", "record": I(1, "PAY-REC", "X(80)")}],
    "ws": [
        I(1, "WS-PAY-STATUS", "X(2)"),
        I(1, "WS-EMP", copy=[CP("PAYTPL", replacing=(":TAG:", "EMP"))], horror=H16),
        I(1, "WS-CONST", copy=[CP("PAYCON", quoted=True)], horror=H16),
        I(1, "WS-LOCAL-DATE", copy=["DATEWS"], horror=H34),
        I(1, "WS-SHARED-DATE", copy=[CP("DATEWS", lib="SHRCPY")], horror=H34),
    ],
    "units": [
        section("MAINLINE", horror=H31),
        para("0100",
             raw("OPEN OUTPUT PAY-FILE", "MOVE SPACES TO EMP-NAME"),
             perform("0200"),
             call("PAYCALC", horror=H31),
             call("PAYRPT", horror=H31),
             raw("CLOSE PAY-FILE"),
             goback(),
             horror=H22),
        para("0200", raw("MOVE 'E00001' TO EMP-ID", "MOVE PC-MAX-HOURS TO WS-PAY-STATUS"), horror=H22),
    ],
    "nested": [PAYCALC],
    "siblings": [PAYRPT],
}

JOBS = [
    {
        "name": "PAYWKLY",
        "title": "WEEKLY PAYROLL",
        "accounting": "(PAYR,0700)",
        "steps": [
            {"name": "PAY", "pgm": "PAYMAIN", "dds": [
                {"name": "STEPLIB", "dsn": "PROD.PAYR.LOADLIB", "disp": ("SHR",)},
                {"name": "PAYOUT", "dsn": "PROD.PAYR.REGISTER", "gen": "+1", "disp": ("NEW", "CATLG", "DELETE"),
                 "extra": ["SPACE=(TRK,(50,10),RLSE)"], "horror": "H-0011"},
            ]},
        ],
    },
]

APP = {
    "id": "PAYR",
    "title": "Payroll (batch, multi-program source)",
    "style": "unnumbered; nested and sibling programs in one member; every COPY form",
    "copybooks": COPYBOOKS,
    "programs": [PAYMAIN],
    "jcl": JOBS,
}
