000100* BILREC   - BILLING RECORD (110 BYTES)
000200 01  BIL-RECORD.
000300     05  BIL-KEY.
000400         10  BIL-ACCT               PIC X(10).
000500         10  BIL-CYCLE              PIC 9(6).
000600     05  BIL-KEY-R              REDEFINES BIL-KEY.
000700         10  BIL-KEY-ALL            PIC X(16).
000800     05  BIL-CUST.
BL0412         10  BIL-NAME               PIC X(30).
001000         10  BIL-ADDR.
001100             15  BIL-STREET             PIC X(30).
BL0412             15  BIL-ZIP                PIC X(10).
001300     05  BIL-AMOUNT             PIC S9(9)V99 COMP-3.
001400     05  BIL-TAX                PIC S9(7)V99 COMP-3.
001500     05  FILLER                 PIC X(4).
001600 01  BIL-TRAILER-COUNT      PIC 9(7).
