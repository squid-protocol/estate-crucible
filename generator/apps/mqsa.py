"""MQSA -- Warlords of the Message Seas, the third Open World level estate (gitgalaxy#7065, #4892 MQ).
A batch shop that feeds orders to a queue, drains them, replies, and inspects queue depth through the
MQ programming interface from COBOL. The programs CALL the MQI verbs; the structures are stand-in
copybooks written for this estate (IBM's MQ copybooks are not shipped, so no field here is a copy of one).

Planted: H-0086 (MQPUT1 with no MQOPEN), H-0087 (MQGET with wait, loop ends on reason 2033), H-0088 (MQCMIT
and MQBACK), H-0089 (MQINQ over a selector block), H-0090 (the MQI structures arrive by COPY), H-0091 (the
batch step: STEPLIB concatenation holding the MQ load libraries).
Slice 2: H-0092 (MQCONNX, the connect call that takes an options structure by COPY) and H-0093 (MQSET, the
attribute-setting sibling of MQINQ, opened with the set option)."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H86, H87, H88, H89, H90, H91 = "H-0086", "H-0087", "H-0088", "H-0089", "H-0090", "H-0091"
H92, H93 = "H-0092", "H-0093"

COPYBOOKS = [
    {"member": "MQSMD",
     "header": [" MQSMD    - MESSAGE DESCRIPTOR, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQS-MSGTYPE", "S9(9)", "COMP", value="8"),
               I(5, "MQS-FORMAT", "X(8)", value="'MQSTR   '"),
               I(5, "MQS-PERSIST", "S9(9)", "COMP", value="1"),
               I(5, "MQS-MSGID", "X(24)"),
               I(5, "MQS-CORRELID", "X(24)"),
               I(5, "MQS-REPLYQ", "X(48)")]},
    {"member": "MQSOD",
     "header": [" MQSOD    - OBJECT DESCRIPTOR, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQS-OBJTYPE", "S9(9)", "COMP", value="1"),
               I(5, "MQS-OBJNAME", "X(48)"),
               I(5, "MQS-OBJQMGR", "X(48)")]},
    {"member": "MQSGMO",
     "header": [" MQSGMO   - GET OPTIONS, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQS-GMO-OPTIONS", "S9(9)", "COMP", value="0"),
               I(5, "MQS-GMO-WAITINT", "S9(9)", "COMP", value="0"),
               I(5, "MQS-GMO-MATCH", "S9(9)", "COMP", value="0")]},
    {"member": "MQSPMO",
     "header": [" MQSPMO   - PUT OPTIONS, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQS-PMO-OPTIONS", "S9(9)", "COMP", value="0"),
               I(5, "MQS-PMO-CONTEXT", "S9(9)", "COMP", value="0")]},
    {"member": "MQSCNO",
     "header": [" MQSCNO   - CONNECT OPTIONS, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQS-CNO-VERSION", "S9(9)", "COMP", value="2"),
               I(5, "MQS-CNO-OPTIONS", "S9(9)", "COMP", value="0"),
               I(5, "MQS-CNO-APPNAME", "X(28)")]},
]

AUTHOR = "ORDER SYSTEMS"
ERA = {"era": 2, "era_evidence": "END-IF (COBOL-85); the MQI is a static CALL interface with no later construct"}


def _common_ws(*extra):
    return [
        I(1, "WS-QMGR", "X(48)", value="'QM01'"),
        I(1, "WS-HCONN", "S9(9)", "COMP", value="0"),
        I(1, "WS-HOBJ", "S9(9)", "COMP", value="0"),
        I(1, "WS-COMPCODE", "S9(9)", "COMP", value="0"),
        I(1, "WS-REASON", "S9(9)", "COMP", value="0"),
        I(1, "WS-OO-OPTIONS", "S9(9)", "COMP", value="0"),
        I(1, "WS-CO-OPTIONS", "S9(9)", "COMP", value="0"),
        I(1, "WS-BUFLEN", "S9(9)", "COMP", value="80"),
        I(1, "WS-DATALEN", "S9(9)", "COMP", value="0"),
        I(1, "WS-BUF", "X(80)"),
        *extra,
    ]


def _fail(prog, text):
    return if_("WS-COMPCODE NOT = 0",
               [raw(f"DISPLAY '{prog} {text} ' WS-REASON", "MOVE 12 TO RETURN-CODE"), goback()])


MQSAPUT = {
    "member": "MQSAPUT", **ERA,
    "program_id": "MQSAPUT", "author": AUTHOR,
    "remarks": ["MQSAPUT - PUT TWO ORDERS ON THE ORDER QUEUE AND COMMIT."],
    "ws": _common_ws(I(1, "WS-MD", copy=["MQSMD"]), I(1, "WS-OD", copy=["MQSOD"]),
                     I(1, "WS-PMO", copy=["MQSPMO"])),
    "units": [
        para("0000-MAIN",
             call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAPUT", "CONNECT FAILED"),
             perform("1000-OPEN"),
             perform("2000-PUT"),
             call("MQCMIT", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             goback()),
        para("1000-OPEN",
             raw("MOVE 'ORDERS.IN' TO MQS-OBJNAME", "MOVE 16 TO WS-OO-OPTIONS"),
             call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                   "WS-REASON"]),
             _fail("MQSAPUT", "OPEN FAILED")),
        para("2000-PUT",
             raw("MOVE 2 TO MQS-PMO-OPTIONS", "MOVE 'ORDER ORD00001 100' TO WS-BUF"),
             call("MQPUT", using=["WS-HCONN", "WS-HOBJ", "WS-MD", "WS-PMO", "WS-BUFLEN", "WS-BUF",
                                  "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAPUT", "PUT FAILED"),
             raw("MOVE 'ORDER ORD00002 250' TO WS-BUF"),
             call("MQPUT", using=["WS-HCONN", "WS-HOBJ", "WS-MD", "WS-PMO", "WS-BUFLEN", "WS-BUF",
                                  "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAPUT", "PUT FAILED")),
    ],
}

MQSAGET = {
    "member": "MQSAGET", **ERA,
    "program_id": "MQSAGET", "author": AUTHOR,
    "remarks": ["MQSAGET - DRAIN THE ORDER QUEUE UNDER SYNCPOINT.",
                "THE LOOP ENDS ON REASON 2033 (NO MESSAGE)."],
    "ws": _common_ws(
        I(1, "WS-MD", copy=["MQSMD"], horror=H90), I(1, "WS-OD", copy=["MQSOD"], horror=H90),
        I(1, "WS-GMO", copy=["MQSGMO"], horror=H90),
        I(1, "WS-DONE-FLAG", "X", value="'N'", kids=[I(88, "WS-DONE", value="'Y'")]),
        I(1, "WS-COUNT", "9(5)", value="ZERO")),
    "units": [
        para("0000-MAIN",
             call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAGET", "CONNECT FAILED"),
             raw("MOVE 'ORDERS.IN' TO MQS-OBJNAME", "MOVE 1 TO WS-OO-OPTIONS"),
             call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                   "WS-REASON"]),
             _fail("MQSAGET", "OPEN FAILED"),
             perform("1000-GET", until="WS-DONE"),
             perform("3000-FINISH"),
             goback()),
        para("1000-GET",
             raw("MOVE 3 TO MQS-GMO-OPTIONS", "MOVE 5000 TO MQS-GMO-WAITINT"),
             call("MQGET", using=["WS-HCONN", "WS-HOBJ", "WS-MD", "WS-GMO", "WS-BUFLEN", "WS-BUF",
                                  "WS-DATALEN", "WS-COMPCODE", "WS-REASON"], horror=H87),
             if_("WS-COMPCODE = 0", [perform("2000-HANDLE")],
                 [if_("WS-REASON = 2033", [raw("SET WS-DONE TO TRUE")],
                      [perform("9000-BACKOUT")])]),
             horror=H87),
        para("2000-HANDLE",
             raw("ADD 1 TO WS-COUNT")),
        para("3000-FINISH",
             call("MQCMIT", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"], horror=H88),
             call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             raw("DISPLAY 'MQSAGET ORDERS ' WS-COUNT")),
        para("9000-BACKOUT",
             call("MQBACK", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"], horror=H88),
             raw("DISPLAY 'MQSAGET BACKED OUT ' WS-REASON", "MOVE 8 TO RETURN-CODE", "SET WS-DONE TO TRUE")),
    ],
}

MQSAREP = {
    "member": "MQSAREP", **ERA,
    "program_id": "MQSAREP", "author": AUTHOR,
    "remarks": ["MQSAREP - ONE REPLY WITH MQPUT1: NO MQOPEN, NO MQCLOSE."],
    "ws": _common_ws(I(1, "WS-MD", copy=["MQSMD"]), I(1, "WS-OD", copy=["MQSOD"]),
                     I(1, "WS-PMO", copy=["MQSPMO"])),
    "units": [
        para("0000-MAIN",
             call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAREP", "CONNECT FAILED"),
             raw("MOVE 'ORDERS.REPLY' TO MQS-OBJNAME", "MOVE 'ORDER ORD00001 ACCEPTED' TO WS-BUF"),
             call("MQPUT1", using=["WS-HCONN", "WS-OD", "WS-MD", "WS-PMO", "WS-BUFLEN", "WS-BUF",
                                   "WS-COMPCODE", "WS-REASON"], horror=H86),
             if_("WS-COMPCODE NOT = 0", [raw("DISPLAY 'MQSAREP PUT1 FAILED ' WS-REASON")]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             goback(), horror=H86),
    ],
}

MQSAINQ = {
    "member": "MQSAINQ", **ERA,
    "program_id": "MQSAINQ", "author": AUTHOR,
    "remarks": ["MQSAINQ - DEPTH OF THE ORDER QUEUE, ONE MQINQ."],
    "ws": _common_ws(
        I(1, "WS-OD", copy=["MQSOD"]),
        I(1, "WS-SEL-COUNT", "S9(9)", "COMP", value="2"),
        I(1, "WS-SEL-BLOCK", kids=[I(5, "WS-SEL-DEPTH", "S9(9)", "COMP", value="3", horror=H89),
                                   I(5, "WS-SEL-MAX", "S9(9)", "COMP", value="15", horror=H89)]),
        I(1, "WS-INT-COUNT", "S9(9)", "COMP", value="2"),
        I(1, "WS-INT-BLOCK", kids=[I(5, "WS-DEPTH", "S9(9)", "COMP", value="0"),
                                   I(5, "WS-MAXDEPTH", "S9(9)", "COMP", value="0")]),
        I(1, "WS-CHAR-LEN", "S9(9)", "COMP", value="0"),
        I(1, "WS-CHAR-ATTRS", "X(8)")),
    "units": [
        para("0000-MAIN",
             call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSAINQ", "CONNECT FAILED"),
             raw("MOVE 'ORDERS.IN' TO MQS-OBJNAME", "MOVE 32 TO WS-OO-OPTIONS"),
             call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                   "WS-REASON"]),
             _fail("MQSAINQ", "OPEN FAILED"),
             call("MQINQ", using=["WS-HCONN", "WS-HOBJ", "WS-SEL-COUNT", "WS-SEL-BLOCK", "WS-INT-COUNT",
                                  "WS-INT-BLOCK", "WS-CHAR-LEN", "WS-CHAR-ATTRS", "WS-COMPCODE",
                                  "WS-REASON"], horror=H89),
             if_("WS-COMPCODE = 0", [raw("DISPLAY 'MQSAINQ DEPTH ' WS-DEPTH ' OF ' WS-MAXDEPTH")]),
             call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             goback()),
    ],
}

MQSACNX = {
    "member": "MQSACNX", **ERA,
    "program_id": "MQSACNX", "author": AUTHOR,
    "remarks": ["MQSACNX - CONNECT WITH MQCONNX AND AN OPTIONS STRUCTURE."],
    "ws": _common_ws(I(1, "WS-CNO", copy=["MQSCNO"], horror=H92), I(1, "WS-OD", copy=["MQSOD"])),
    "units": [
        para("0000-MAIN",
             raw("MOVE 'MQSACNX' TO MQS-CNO-APPNAME", "MOVE 2 TO MQS-CNO-OPTIONS"),
             call("MQCONNX", using=["WS-QMGR", "WS-CNO", "WS-HCONN", "WS-COMPCODE", "WS-REASON"],
                  horror=H92),
             _fail("MQSACNX", "CONNECT FAILED"),
             raw("MOVE 'ORDERS.IN' TO MQS-OBJNAME", "MOVE 1 TO WS-OO-OPTIONS"),
             call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                   "WS-REASON"]),
             _fail("MQSACNX", "OPEN FAILED"),
             call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             goback(), horror=H92),
    ],
}

MQSASET = {
    "member": "MQSASET", **ERA,
    "program_id": "MQSASET", "author": AUTHOR,
    "remarks": ["MQSASET - INHIBIT PUTS ON THE ORDER QUEUE, ONE MQSET."],
    "ws": _common_ws(
        I(1, "WS-OD", copy=["MQSOD"]),
        I(1, "WS-SEL-COUNT", "S9(9)", "COMP", value="1"),
        I(1, "WS-SEL-BLOCK", kids=[I(5, "WS-SEL-INHIBIT", "S9(9)", "COMP", value="6", horror=H93)]),
        I(1, "WS-INT-COUNT", "S9(9)", "COMP", value="1"),
        I(1, "WS-INT-BLOCK", kids=[I(5, "WS-INHIBIT-PUT", "S9(9)", "COMP", value="1", horror=H93)]),
        I(1, "WS-CHAR-LEN", "S9(9)", "COMP", value="0"),
        I(1, "WS-CHAR-ATTRS", "X(8)")),
    "units": [
        para("0000-MAIN",
             call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             _fail("MQSASET", "CONNECT FAILED"),
             raw("MOVE 'ORDERS.IN' TO MQS-OBJNAME", "MOVE 64 TO WS-OO-OPTIONS"),
             call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                   "WS-REASON"]),
             _fail("MQSASET", "OPEN FAILED"),
             call("MQSET", using=["WS-HCONN", "WS-HOBJ", "WS-SEL-COUNT", "WS-SEL-BLOCK", "WS-INT-COUNT",
                                  "WS-INT-BLOCK", "WS-CHAR-LEN", "WS-CHAR-ATTRS", "WS-COMPCODE",
                                  "WS-REASON"], horror=H93),
             if_("WS-COMPCODE NOT = 0", [raw("DISPLAY 'MQSASET SET FAILED ' WS-REASON")]),
             call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
             call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
             goback()),
    ],
}


def _dd(name, dsn=None, disp=("SHR",), **kw):
    return {"name": name, "dsn": dsn, "disp": disp, **kw}


LOADLIB = "PROD.MQSA.LOADLIB"


def _mq_steplib(horror=None):
    return [_dd("STEPLIB", LOADLIB, horror=horror),
            _dd("", "MQM.SCSQAUTH", concat=True, horror=horror),
            _dd("", "MQM.SCSQLOAD", concat=True, horror=horror)]


JOBS = [{
    "name": "MQSARUN",
    "title": "MQSA ORDER FLOW",
    "accounting": "(MQSA,0100)",
    "comments": ["PUT, DRAIN, REPLY AND INQUIRE; THE MQ LOAD LIBRARIES RIDE IN THE STEPLIB CONCATENATION"],
    "steps": [
        {"name": "PUT010", "pgm": "MQSAPUT", "dds": [*_mq_steplib(H91), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "GET020", "pgm": "MQSAGET", "dds": [*_mq_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "REP030", "pgm": "MQSAREP", "dds": [*_mq_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "INQ040", "pgm": "MQSAINQ", "dds": [*_mq_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "CNX050", "pgm": "MQSACNX", "dds": [*_mq_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "SET060", "pgm": "MQSASET", "dds": [*_mq_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
    ],
}]

APP = {
    "id": "MQSA",
    "era": 2,
    "era_evidence": "END-IF (COBOL-85); static CALLs to the MQI and plain EXEC steps",
    "title": "Warlords of the Message Seas (batch MQ: the MQI beyond the core calls)",
    "style": "batch COBOL over the MQ programming interface: MQPUT1, MQGET with wait, MQCMIT / MQBACK, MQINQ, MQCONNX, MQSET",
    "copybooks": COPYBOOKS,
    "dclgen": [],
    "programs": [MQSAPUT, MQSAGET, MQSAREP, MQSAINQ, MQSACNX, MQSASET],
    "jcl": JOBS,
    "procs": [],
}
