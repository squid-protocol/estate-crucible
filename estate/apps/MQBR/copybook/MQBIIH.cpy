      * MQBIIH   - IMS HEADER, ESTATE STAND-IN, 84 BYTES
           10  MQB-IIH-STRUCID        PIC X(4) VALUE 'IIH '.
           10  MQB-IIH-VERSION        PIC S9(9) COMP VALUE 1.
           10  MQB-IIH-LENGTH         PIC S9(9) COMP VALUE 84.
           10  MQB-IIH-ENCODING       PIC S9(9) COMP VALUE 0.
           10  MQB-IIH-CCSID          PIC S9(9) COMP VALUE 0.
           10  MQB-IIH-FORMAT         PIC X(8).
           10  MQB-IIH-FLAGS          PIC S9(9) COMP VALUE 0.
           10  MQB-IIH-LTERM          PIC X(8).
           10  MQB-IIH-MFSMAP         PIC X(8).
           10  MQB-IIH-REPLYFMT       PIC X(8).
           10  MQB-IIH-AUTH           PIC X(8).
           10  MQB-IIH-TRANINST       PIC X(16) VALUE LOW-VALUES.
           10  MQB-IIH-TRANSTATE      PIC X VALUE ' '.
           10  MQB-IIH-COMMIT         PIC X VALUE '0'.
           10  MQB-IIH-SECURITY       PIC X VALUE 'C'.
           10  MQB-IIH-RESERVED       PIC X VALUE ' '.
