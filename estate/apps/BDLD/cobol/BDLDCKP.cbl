       IDENTIFICATION DIVISION.
       PROGRAM-ID.    BDLDCKP.
       AUTHOR.       BATCH OPERATIONS.
      *------------------------------------------------------------
      * BDLDCKP - COUNT THE TRANSACTION EXTRACT.
      * CHECKPOINT EVERY 1000 RECORDS (RERUN CLAUSE) TO THE SYSCKPT DD.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRAN-FILE ASSIGN TO TRANIN
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-TRAN-STATUS.
       I-O-CONTROL.
           RERUN ON SYSCKPT EVERY 1000 RECORDS OF TRAN-FILE.
       DATA DIVISION.
       FILE SECTION.
       FD  TRAN-FILE
           RECORDING MODE IS F.
       01  TRAN-REC.
           COPY BDLREC.
       WORKING-STORAGE SECTION.
       01  WS-TRAN-STATUS         PIC X(2).
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-COUNT               PIC 9(7) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT TRAN-FILE
           PERFORM 8000-READ
           PERFORM 1000-COUNT UNTIL WS-EOF
           CLOSE TRAN-FILE
           DISPLAY 'BDLDCKP COUNTED ' WS-COUNT
           GOBACK.
       1000-COUNT.
           ADD 1 TO WS-COUNT
           PERFORM 8000-READ.
       8000-READ.
           READ TRAN-FILE
              AT END
                 SET WS-EOF TO TRUE
           END-READ.
