"""MQBR -- the Bridge Road, an Open World level estate (gitgalaxy#7065, #4892 MQ).
A shop that starts IMS and CICS work by putting messages on bridge queues. The IMS bridge and the CICS bridge
read a message whose MQMD Format names a header structure (MQIIH, MQCIH) that carries the bridge's own control
fields, then the application data. Two sender programs build those messages, and one IMS message processing
program is the transaction a bridge message starts. The structures are stand-in copybooks written for this
estate at the lengths and field order IBM documents (MQIIH 84 bytes, MQCIH version 2 180 bytes); no field here
is a copy of an IBM copybook.

Planted: H-0114 (a message with an MQIIH and LLZZ-framed transaction data, MQMD format MQFMT_IMS),
H-0115 (a message with an MQCIH for a DPL program request, MQMD format MQFMT_CICS), H-0116 (the IMS transaction
program that GUs its input from the IO PCB and ISRTs the reply to the IO PCB, which the IMS bridge returns to the
reply-to queue).
Not planted: the IMS region JCL (DFSRRC00), PSB and the bridge queue definitions; the DPL program the CICS bridge
links to. Later slices, each needs its own verified quote."""

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

H114, H115, H116 = "H-0114", "H-0115", "H-0116"

AUTHOR = "BRIDGE SYSTEMS"
ERA = {"era": 2, "era_evidence": "END-IF (COBOL-85); the MQI and DL/I are static CALL interfaces"}


def _iih():
    # MQIIH, 84 bytes: 5 four-byte fields, Format 8, Flags 4, four 8-byte fields, 16, four 1-byte fields
    return [I(10, "MQB-IIH-STRUCID", "X(4)", value="'IIH '"),
            I(10, "MQB-IIH-VERSION", "S9(9)", "COMP", value="1"),
            I(10, "MQB-IIH-LENGTH", "S9(9)", "COMP", value="84"),
            I(10, "MQB-IIH-ENCODING", "S9(9)", "COMP", value="0"),
            I(10, "MQB-IIH-CCSID", "S9(9)", "COMP", value="0"),
            I(10, "MQB-IIH-FORMAT", "X(8)"),
            I(10, "MQB-IIH-FLAGS", "S9(9)", "COMP", value="0"),
            I(10, "MQB-IIH-LTERM", "X(8)"),
            I(10, "MQB-IIH-MFSMAP", "X(8)"),
            I(10, "MQB-IIH-REPLYFMT", "X(8)"),
            I(10, "MQB-IIH-AUTH", "X(8)"),
            I(10, "MQB-IIH-TRANINST", "X(16)", value="LOW-VALUES"),
            I(10, "MQB-IIH-TRANSTATE", "X", value="' '"),
            I(10, "MQB-IIH-COMMIT", "X", value="'0'"),
            I(10, "MQB-IIH-SECURITY", "X", value="'C'"),
            I(10, "MQB-IIH-RESERVED", "X", value="' '")]


def _cih():
    # MQCIH version 2, 180 bytes, in IBM's field order
    f = [("STRUCID", "X(4)", "'CIH '"), ("VERSION", "S9(9)", "2"), ("LENGTH", "S9(9)", "180"),
         ("ENCODING", "S9(9)", "0"), ("CCSID", "S9(9)", "0"), ("FORMAT", "X(8)", None),
         ("FLAGS", "S9(9)", "0"), ("RETURNCODE", "S9(9)", "0"), ("COMPCODE", "S9(9)", "0"),
         ("REASON", "S9(9)", "0"), ("UOWCONTROL", "S9(9)", "273"), ("GETWAIT", "S9(9)", "-2"),
         ("LINKTYPE", "S9(9)", "1"), ("OUTDATALEN", "S9(9)", "-1"), ("FACKEEP", "S9(9)", "0"),
         ("ADSDESC", "S9(9)", "0"), ("CONVTASK", "S9(9)", "0"), ("TASKEND", "S9(9)", "0"),
         ("FACILITY", "X(8)", "LOW-VALUES"), ("FUNCTION", "X(4)", None), ("ABENDCODE", "X(4)", None),
         ("AUTH", "X(8)", None), ("RESERVED1", "X(8)", None), ("REPLYFMT", "X(8)", None),
         ("REMOTESYS", "X(4)", None), ("REMOTETRAN", "X(4)", None), ("TRANID", "X(4)", None),
         ("FACLIKE", "X(4)", None), ("AID", "X(4)", None), ("STARTCODE", "X(4)", None),
         ("CANCELCODE", "X(4)", None), ("NEXTTRAN", "X(4)", None), ("RESERVED2", "X(8)", None),
         ("RESERVED3", "X(8)", None), ("CURSOR", "S9(9)", "0"), ("ERROFFSET", "S9(9)", "0"),
         ("INPUTITEM", "S9(9)", "0"), ("RESERVED4", "S9(9)", "0")]
    return [I(10, f"MQB-CIH-{n}", p, "COMP" if p.startswith("S9") else None, value=v) for n, p, v in f]


COPYBOOKS = [
    {"member": "MQBMD",
     "header": [" MQBMD    - MESSAGE DESCRIPTOR, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQB-MSGTYPE", "S9(9)", "COMP", value="8"),
               I(5, "MQB-FORMAT", "X(8)"),
               I(5, "MQB-PERSIST", "S9(9)", "COMP", value="1"),
               I(5, "MQB-MSGID", "X(24)"),
               I(5, "MQB-REPLYQ", "X(48)")]},
    {"member": "MQBOD",
     "header": [" MQBOD    - OBJECT DESCRIPTOR, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQB-OBJTYPE", "S9(9)", "COMP", value="1"),
               I(5, "MQB-OBJNAME", "X(48)"),
               I(5, "MQB-OBJQMGR", "X(48)")]},
    {"member": "MQBPMO",
     "header": [" MQBPMO   - PUT OPTIONS, STAND-IN WRITTEN FOR THIS ESTATE"],
     "items": [I(5, "MQB-PMO-OPTIONS", "S9(9)", "COMP", value="0"),
               I(5, "MQB-PMO-CONTEXT", "S9(9)", "COMP", value="0")]},
    {"member": "MQBIIH",
     "header": [" MQBIIH   - IMS HEADER, ESTATE STAND-IN, 84 BYTES"],
     "items": _iih()},
    {"member": "MQBCIH",
     "header": [" MQBCIH   - CICS HEADER V2, ESTATE STAND-IN, 180 BYTES"],
     "items": _cih()},
]


def _ws(*extra):
    return [
        I(1, "WS-QMGR", "X(48)", value="'QM01'"),
        I(1, "WS-HCONN", "S9(9)", "COMP", value="0"),
        I(1, "WS-HOBJ", "S9(9)", "COMP", value="0"),
        I(1, "WS-COMPCODE", "S9(9)", "COMP", value="0"),
        I(1, "WS-REASON", "S9(9)", "COMP", value="0"),
        I(1, "WS-OO-OPTIONS", "S9(9)", "COMP", value="0"),
        I(1, "WS-CO-OPTIONS", "S9(9)", "COMP", value="0"),
        I(1, "WS-MD", copy=["MQBMD"]), I(1, "WS-OD", copy=["MQBOD"]), I(1, "WS-PMO", copy=["MQBPMO"]),
        *extra,
    ]


def _fail(prog, text):
    return if_("WS-COMPCODE NOT = 0",
               [raw(f"DISPLAY '{prog} {text} ' WS-REASON", "MOVE 12 TO RETURN-CODE"), goback()])


def _sender(prog, remark, queue, msg_len, set_up, msg_horror):
    put = call("MQPUT", using=["WS-HCONN", "WS-HOBJ", "WS-MD", "WS-PMO", "WS-MSGLEN", "WS-MSG",
                               "WS-COMPCODE", "WS-REASON"], horror=msg_horror)
    return {
        "member": prog, **ERA, "program_id": prog, "author": AUTHOR, "remarks": remark,
        "ws": _ws(I(1, "WS-MSGLEN", "S9(9)", "COMP", value=str(msg_len)), *set_up["ws"]),
        "units": [
            para("0000-MAIN",
                 call("MQCONN", using=["WS-QMGR", "WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
                 _fail(prog, "CONNECT FAILED"),
                 raw(f"MOVE '{queue}' TO MQB-OBJNAME", "MOVE 16 TO WS-OO-OPTIONS"),
                 call("MQOPEN", using=["WS-HCONN", "WS-OD", "WS-OO-OPTIONS", "WS-HOBJ", "WS-COMPCODE",
                                       "WS-REASON"]),
                 _fail(prog, "OPEN FAILED"),
                 perform("1000-BUILD"),
                 put,
                 _fail(prog, "PUT FAILED"),
                 call("MQCMIT", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
                 call("MQCLOSE", using=["WS-HCONN", "WS-HOBJ", "WS-CO-OPTIONS", "WS-COMPCODE", "WS-REASON"]),
                 call("MQDISC", using=["WS-HCONN", "WS-COMPCODE", "WS-REASON"]),
                 goback()),
            para("1000-BUILD", *set_up["build"]),
        ],
    }


# 84 (MQIIH) + LL ZZ (4) + transaction code (8) + data (12) = 108; LL = 4 + 8 + 12 = 24
MQBRIMS = _sender(
    "MQBRIMS",
    ["MQBRIMS - START THE ORDER TRANSACTION IN IMS VIA THE BRIDGE.",
     "MESSAGE: MQIIH, THEN LL ZZ, THE TRANCODE AND THE DATA."],
    "IMS.BRIDGE.ORDQ", 108,
    {"ws": [I(1, "WS-MSG", horror=H114, kids=[
                I(5, "WS-IIH", copy=["MQBIIH"], horror=H114),
                I(5, "WS-LL", "S9(4)", "COMP", value="24", horror=H114),
                I(5, "WS-ZZ", "S9(4)", "COMP", value="0", horror=H114),
                I(5, "WS-TRANCODE", "X(8)", value="'ORDENTRY'", horror=H114),
                I(5, "WS-DATA", "X(12)", value="'ORD00001 100'", horror=H114)])],
     "build": [raw("MOVE 'MQIMS   ' TO MQB-FORMAT", "MOVE 'IMS.BRIDGE.REPLYQ' TO MQB-REPLYQ",
                   "MOVE '1' TO MQB-IIH-COMMIT", "MOVE 'MQSTR   ' TO MQB-IIH-FORMAT")]},
    H114)

# 180 (MQCIH) + COMMAREA (40) = 220
MQBRCIH = _sender(
    "MQBRCIH",
    ["MQBRCIH - RUN A CICS PROGRAM VIA THE CICS DPL BRIDGE.",
     "MESSAGE: MQCIH FOLLOWED BY THE COMMAREA."],
    "CICS.BRIDGE.ORDQ", 220,
    {"ws": [I(1, "WS-MSG", horror=H115, kids=[
                I(5, "WS-CIH", copy=["MQBCIH"], horror=H115),
                I(5, "WS-COMMAREA", "X(40)", value="'ORD00001 100'", horror=H115)])],
     "build": [raw("MOVE 'MQCICS  ' TO MQB-FORMAT", "MOVE 'CICS.BRIDGE.REPLYQ' TO MQB-REPLYQ",
                   "MOVE 'ORDCOMM ' TO MQB-CIH-FORMAT", "MOVE 1 TO MQB-CIH-LINKTYPE",
                   "MOVE 273 TO MQB-CIH-UOWCONTROL")]},
    H115)

MQBRMPP = {
    "member": "MQBRMPP", **ERA,
    "program_id": "MQBRMPP", "author": AUTHOR,
    "remarks": ["MQBRMPP - THE ORDER TRANSACTION THE IMS BRIDGE STARTS.",
                "GU THE INPUT, ISRT THE REPLY TO THE IO PCB."],
    "ws": [
        I(1, "WS-GU", "X(4)", value="'GU  '"),
        I(1, "WS-ISRT", "X(4)", value="'ISRT'"),
        I(1, "WS-IN-AREA", kids=[I(5, "WS-IN-LL", "S9(4)", "COMP"), I(5, "WS-IN-ZZ", "S9(4)", "COMP"),
                                 I(5, "WS-IN-TRAN", "X(8)"), I(5, "WS-IN-DATA", "X(12)")]),
        I(1, "WS-OUT-AREA", kids=[I(5, "WS-OUT-LL", "S9(4)", "COMP", value="22"),
                                  I(5, "WS-OUT-ZZ", "S9(4)", "COMP", value="0"),
                                  I(5, "WS-OUT-TEXT", "X(18)", value="'ORDER ACCEPTED    '")]),
    ],
    "linkage": [
        I(1, "IO-PCB", kids=[I(5, "IO-LTERM", "X(8)"), I(5, "IO-RSV", "X(2)"), I(5, "IO-STATUS", "X(2)")]),
    ],
    "using": ["IO-PCB"],
    "units": [
        para("0000-MAIN",
             call("CBLTDLI", using=["WS-GU", "IO-PCB", "WS-IN-AREA"]),
             if_("IO-STATUS = SPACES", [perform("1000-REPLY")]),
             goback()),
        para("1000-REPLY",
             call("CBLTDLI", using=["WS-ISRT", "IO-PCB", "WS-OUT-AREA"], horror=H116),
             if_("IO-STATUS NOT = SPACES", [raw("DISPLAY 'MQBRMPP ISRT STATUS ' IO-STATUS")]),
             horror=H116),
    ],
}


def _dd(name, dsn=None, disp=("SHR",), **kw):
    return {"name": name, "dsn": dsn, "disp": disp, **kw}


def _steplib():
    return [_dd("STEPLIB", "PROD.MQBR.LOADLIB"),
            _dd("", "MQM.SCSQAUTH", concat=True),
            _dd("", "MQM.SCSQLOAD", concat=True)]


JOBS = [{
    "name": "MQBRRUN",
    "title": "MQBR BRIDGE SENDERS",
    "accounting": "(MQBR,0100)",
    "comments": ["SEND ONE ORDER TO IMS AND ONE TO CICS THROUGH THEIR BRIDGE QUEUES"],
    "steps": [
        {"name": "IMS010", "pgm": "MQBRIMS", "dds": [*_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
        {"name": "CIC020", "pgm": "MQBRCIH", "dds": [*_steplib(), {"name": "SYSOUT", "sysout": "*"}]},
    ],
}]

APP = {
    "id": "MQBR",
    "era": 2,
    "era_evidence": "END-IF (COBOL-85); static CALLs to the MQI and DL/I and plain EXEC steps",
    "title": "Bridge Road (MQ messages that start IMS and CICS work)",
    "style": "batch COBOL senders for the IMS bridge (MQIIH) and the CICS bridge (MQCIH), and the IMS MPP the bridge starts",
    "copybooks": COPYBOOKS,
    "dclgen": [],
    "programs": [MQBRIMS, MQBRCIH, MQBRMPP],
    "jcl": JOBS,
    "procs": [],
}
