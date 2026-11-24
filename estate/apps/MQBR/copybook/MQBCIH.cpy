      * MQBCIH   - CICS HEADER V2, ESTATE STAND-IN, 180 BYTES
           10  MQB-CIH-STRUCID        PIC X(4) VALUE 'CIH '.
           10  MQB-CIH-VERSION        PIC S9(9) COMP VALUE 2.
           10  MQB-CIH-LENGTH         PIC S9(9) COMP VALUE 180.
           10  MQB-CIH-ENCODING       PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-CCSID          PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-FORMAT         PIC X(8).
           10  MQB-CIH-FLAGS          PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-RETURNCODE     PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-COMPCODE       PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-REASON         PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-UOWCONTROL     PIC S9(9) COMP VALUE 273.
           10  MQB-CIH-GETWAIT        PIC S9(9) COMP VALUE -2.
           10  MQB-CIH-LINKTYPE       PIC S9(9) COMP VALUE 1.
           10  MQB-CIH-OUTDATALEN     PIC S9(9) COMP VALUE -1.
           10  MQB-CIH-FACKEEP        PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-ADSDESC        PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-CONVTASK       PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-TASKEND        PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-FACILITY       PIC X(8) VALUE LOW-VALUES.
           10  MQB-CIH-FUNCTION       PIC X(4).
           10  MQB-CIH-ABENDCODE      PIC X(4).
           10  MQB-CIH-AUTH           PIC X(8).
           10  MQB-CIH-RESERVED1      PIC X(8).
           10  MQB-CIH-REPLYFMT       PIC X(8).
           10  MQB-CIH-REMOTESYS      PIC X(4).
           10  MQB-CIH-REMOTETRAN     PIC X(4).
           10  MQB-CIH-TRANID         PIC X(4).
           10  MQB-CIH-FACLIKE        PIC X(4).
           10  MQB-CIH-AID            PIC X(4).
           10  MQB-CIH-STARTCODE      PIC X(4).
           10  MQB-CIH-CANCELCODE     PIC X(4).
           10  MQB-CIH-NEXTTRAN       PIC X(4).
           10  MQB-CIH-RESERVED2      PIC X(8).
           10  MQB-CIH-RESERVED3      PIC X(8).
           10  MQB-CIH-CURSOR         PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-ERROFFSET      PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-INPUTITEM      PIC S9(9) COMP VALUE 0.
           10  MQB-CIH-RESERVED4      PIC S9(9) COMP VALUE 0.
