       IDENTIFICATION DIVISION.
       PROGRAM-ID.    LNRATE                                            
      *------------------------------------------------------------
      * LNRATE - MONTHLY RATE RESET. CALLS LNCALC PER LOAN.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOAN-FILE ASSIGN TO LOANIN
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-LOAN-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  LOAN-FILE
           RECORDING MODE IS F.
       01  LOAN-RECORD.
           COPY LNREC.
       WORKING-STORAGE SECTION.
       01  WS-LOAN-STATUS         PIC X(2).
           88  WS-LOAN-EOF            VALUE '10'.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT LOAN-FILE
           PERFORM 1000-NEXT-LOAN UNTIL WS-LOAN-EOF
           CLOSE LOAN-FILE
           GOBACK.
       1000-NEXT-LOAN.
           READ LOAN-FILE
           IF NOT WS-LOAN-EOF
              CALL 'LNCALC' USING LOAN-RECORD
           END-IF.
