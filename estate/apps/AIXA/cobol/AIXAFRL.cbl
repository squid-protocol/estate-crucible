       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAFRL.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAFRL - PICK SLOT CLAIMS IN AN RRDS.
      * FILE STATUS 22, 23 AND 24 ARE TESTED IN ONE PARAGRAPH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SLOT-FILE ASSIGN TO SLOTS
               ORGANIZATION IS RELATIVE
               ACCESS MODE IS DYNAMIC
               RELATIVE KEY IS WS-SLOT-NO
               FILE STATUS IS WS-SLOT-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  SLOT-FILE
           RECORDING MODE IS F.
       01  SLOT-REC.
           05  SLOT-ID                PIC X(8).
           05  SLOT-QTY               PIC 9(5).
           05  FILLER                 PIC X(27).
       WORKING-STORAGE SECTION.
       01  WS-SLOT-STATUS         PIC X(2).
       01  WS-SLOT-NO             PIC 9(4) VALUE ZERO.
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O SLOT-FILE
           PERFORM 1000-CLAIM
           PERFORM 2000-PROBE
           CLOSE SLOT-FILE
           DISPLAY 'AIXAFRL BAD ' WS-BAD
           GOBACK.
       1000-CLAIM.
           MOVE 3 TO WS-SLOT-NO
           MOVE 'SLOT0003' TO SLOT-ID
           MOVE 12 TO SLOT-QTY
           WRITE SLOT-REC
           END-WRITE
           PERFORM 9000-STATUS
           WRITE SLOT-REC
           END-WRITE
           PERFORM 9000-STATUS.
       2000-PROBE.
           MOVE 9 TO WS-SLOT-NO
           READ SLOT-FILE
           END-READ
           PERFORM 9000-STATUS.
       9000-STATUS.
           IF WS-SLOT-STATUS = '22'
              DISPLAY 'SLOT ALREADY CLAIMED'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-SLOT-STATUS = '23'
                 DISPLAY 'SLOT NOT FOUND'
                 ADD 1 TO WS-BAD
              ELSE
                 IF WS-SLOT-STATUS = '24'
                    DISPLAY 'SLOT BEYOND FILE'
                    ADD 1 TO WS-BAD
                 END-IF
              END-IF
           END-IF.
