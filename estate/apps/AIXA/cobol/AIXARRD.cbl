       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXARRD.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXARRD - PICK SLOTS IN AN RRDS, BY RELATIVE NUMBER.
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
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O SLOT-FILE
           PERFORM 1000-PUT
           CLOSE SLOT-FILE
           GOBACK.
       1000-PUT.
           MOVE 3 TO WS-SLOT-NO
           MOVE 'SLOT0003' TO SLOT-ID
           MOVE 12 TO SLOT-QTY
           WRITE SLOT-REC
               INVALID KEY DISPLAY 'SLOT TAKEN'
           END-WRITE
           MOVE 9 TO WS-SLOT-NO
           READ SLOT-FILE
               INVALID KEY DISPLAY 'SLOT EMPTY'
           END-READ
           IF WS-SLOT-STATUS = '23'
              MOVE 4 TO RETURN-CODE
           END-IF.
