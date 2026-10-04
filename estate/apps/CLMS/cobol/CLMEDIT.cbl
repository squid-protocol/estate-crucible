       IDENTIFICATION DIVISION.
       PROGRAM-ID.    CLMEDIT.
       AUTHOR.       CLAIMS.
      *------------------------------------------------------------
      * CLMEDIT - EDIT ONE CLAIM. CALLED FROM PL/I (CLMPROC).
      *------------------------------------------------------------
       DATA DIVISION.
       LINKAGE SECTION.
       01  LK-CLAIM.
           05  LK-CLM-ID              PIC X(10).
           05  LK-CLM-AMT             PIC S9(7)V99 COMP-3.
           05  LK-CLM-STATUS          PIC X.
       PROCEDURE DIVISION USING LK-CLAIM.
       0000-MAIN.
           IF LK-CLM-AMT > 1000000
              MOVE 'R' TO LK-CLM-STATUS
           END-IF
           GOBACK.
