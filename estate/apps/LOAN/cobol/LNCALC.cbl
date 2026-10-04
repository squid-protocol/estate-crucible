       IDENTIFICATION DIVISION.
       PROGRAM-ID LNCALC.
       AUTHOR.       LOAN SYSTEMS.
      *------------------------------------------------------------
      * LNCALC - LEVEL PAYMENT FOR ONE LOAN. CALLED BY LNRATE.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MONTHLY-RATE        PIC S9(3)V9(8) COMP-3.
       LINKAGE SECTION.
       01  LK-LOAN.
           COPY LNREC.
       PROCEDURE DIVISION USING LK-LOAN.
       0000-MAIN.
           COMPUTE WS-MONTHLY-RATE = LN-RATE / 1200
           COMPUTE LN-PAYMENT ROUNDED = LN-PRINCIPAL * WS-MONTHLY-RATE
           GOBACK.
