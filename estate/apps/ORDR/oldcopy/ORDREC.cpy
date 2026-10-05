      * ORDREC   - ORDER RECORD (1994 LAYOUT, 36 BYTES). DO NOT USE.
           05  ORD-ID                 PIC X(10).
           05  ORD-CUST               PIC X(8).
           05  ORD-ITEM               PIC X(8).
           05  ORD-QTY                PIC 9(5).
           05  ORD-STATUS             PIC X.
           88  ORD-OPEN               VALUE 'O'.
           88  ORD-REJECTED           VALUE 'R'.
           05  FILLER                 PIC X(4).
