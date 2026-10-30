       IDENTIFICATION DIVISION.
       PROGRAM-ID.    BDLDDB2.
       AUTHOR.       BATCH OPERATIONS.
      *------------------------------------------------------------
      * BDLDDB2 - LOAD THE SORTED EXTRACT INTO BDLD_SUMMARY.
      * RUNS UNDER IKJEFT01 (DSN RUN PROGRAM), STEP LOAD020.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SORTED-FILE ASSIGN TO SORTED
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-SORTED-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  SORTED-FILE
           RECORDING MODE IS F.
       01  SORTED-REC.
           COPY BDLREC.
       WORKING-STORAGE SECTION.
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL INCLUDE DCLBDLD END-EXEC.
       01  WS-SORTED-STATUS       PIC X(2).
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-LOADED              PIC 9(7) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT SORTED-FILE
           PERFORM 8000-READ
           PERFORM 1000-LOAD UNTIL WS-EOF
           CLOSE SORTED-FILE
           DISPLAY 'BDLDDB2 LOADED ' WS-LOADED
           GOBACK.
       1000-LOAD.
           MOVE BDL-ACCT TO ACCT-ID
           MOVE BDL-AMT TO TOTAL-AMT
           EXEC SQL
               INSERT INTO PROD.BDLD_SUMMARY (ACCT_ID, TOTAL_AMT)
                 VALUES (:ACCT-ID, :TOTAL-AMT)
           END-EXEC
           IF SQLCODE = 0
              ADD 1 TO WS-LOADED
           ELSE
              MOVE 8 TO RETURN-CODE
              SET WS-EOF TO TRUE
           END-IF
           PERFORM 8000-READ.
       8000-READ.
           READ SORTED-FILE
              AT END
                 SET WS-EOF TO TRUE
           END-READ.
