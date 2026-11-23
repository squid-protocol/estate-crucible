       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAMOD.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAMOD - LOGIC-ERROR FILE STATUS 4X OVER A KSDS.
      * EACH STATEMENT IS TRIED IN A STATE THAT DOES NOT ALLOW IT.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUS-FILE ASSIGN TO CUSKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS CUS-ID
               FILE STATUS IS WS-CUS-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  CUS-FILE
           RECORDING MODE IS F.
       01  CUS-REC.
           05  CUS-ID                 PIC X(8).
           05  CUS-TAX                PIC X(9).
           05  CUS-NAME               PIC X(20).
           05  FILLER                 PIC X(3).
       WORKING-STORAGE SECTION.
       01  WS-CUS-STATUS          PIC X(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT CUS-FILE
           PERFORM 1000-WRONG-MODE
           MOVE '00' TO WS-CUS-STATUS
           PERFORM 2000-DRAIN UNTIL WS-CUS-STATUS NOT = '00'
           PERFORM 2100-PAST-END
           PERFORM 3000-REOPEN
           CLOSE CUS-FILE
           PERFORM 4000-CLOSED
           DISPLAY 'AIXAMOD BAD ' WS-BAD
           GOBACK.
       1000-WRONG-MODE.
           MOVE 'CUS00009' TO CUS-ID
           WRITE CUS-REC
           IF WS-CUS-STATUS = '48'
              DISPLAY 'WRITE ON AN INPUT FILE'
           ELSE
              ADD 1 TO WS-BAD
           END-IF
           REWRITE CUS-REC
           IF WS-CUS-STATUS = '49'
              DISPLAY 'REWRITE ON AN INPUT FILE'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
       2000-DRAIN.
           READ CUS-FILE NEXT RECORD
               AT END CONTINUE
           END-READ.
       2100-PAST-END.
           READ CUS-FILE NEXT RECORD
               AT END CONTINUE
           END-READ
           IF WS-CUS-STATUS = '46'
              DISPLAY 'READ PAST THE END'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
       3000-REOPEN.
           OPEN INPUT CUS-FILE
           IF WS-CUS-STATUS = '41'
              DISPLAY 'FILE ALREADY OPEN'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
       4000-CLOSED.
           READ CUS-FILE NEXT RECORD
               AT END CONTINUE
           END-READ
           IF WS-CUS-STATUS = '47'
              DISPLAY 'READ ON A CLOSED FILE'
           ELSE
              ADD 1 TO WS-BAD
           END-IF
           CLOSE CUS-FILE
           IF WS-CUS-STATUS = '42'
              DISPLAY 'FILE ALREADY CLOSED'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
