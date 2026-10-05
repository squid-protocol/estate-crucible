       IDENTIFICATION DIVISION.
       PROGRAM-ID.    ORDVAL.
       AUTHOR.       M OKAFOR.
       DATE-WRITTEN. 06/02/98.
      *------------------------------------------------------------
      * ORDVAL - EDIT ONE ORDER. CALLED BY ORDMAIN.
      * BACKUP TAKEN 2011-03-02 BEFORE CHG1188 (TK)
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MAX-QTY             PIC S9(5) COMP-3 VALUE 5000.
       LINKAGE SECTION.
       01  LK-ORDER.
           COPY ORDREC.
       01  LK-PARM.
           COPY ORDPARM.
       PROCEDURE DIVISION USING LK-ORDER LK-PARM.
       0000-MAIN.
           MOVE ZERO TO PRM-RC
           PERFORM 1000-CHECK-QTY
           GOBACK.
       1000-CHECK-QTY.
           IF ORD-QTY > WS-MAX-QTY OR ORD-QTY NOT > ZERO
              SET ORD-REJECTED TO TRUE
              MOVE 8 TO PRM-RC
           END-IF.
