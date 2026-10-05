      * ORDREC   - ORDER RECORD, CURRENT LAYOUT (41 BYTES).
      *            CHG0907 ADDED ORD-CHANNEL.
      *            SEE ALSO SHRCPY(ORDREC), ORDROLD(ORDREC).
           05  ORD-ID                 PIC X(10).
           05  ORD-CUST               PIC X(8).
           05  ORD-ITEM               PIC X(12).
           05  ORD-QTY                PIC S9(5) COMP-3.
           05  ORD-PRICE              PIC S9(7)V99 COMP-3.
           05  ORD-STATUS             PIC X.
           88  ORD-OPEN               VALUE 'O'.
           88  ORD-REJECTED           VALUE 'R'.
           05  ORD-CHANNEL            PIC X(2).
