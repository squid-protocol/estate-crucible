       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAFES.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAFES - AUDIT LOG ESDS OPENED THE WRONG WAY ON PURPOSE.
      * FILE STATUS 41, 42, 47, 48 AND 49 ARE TESTED IN ONE PARAGRAPH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOG-FILE ASSIGN TO LOGESD
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-LOG-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  LOG-FILE
           RECORDING MODE IS F.
       01  LOG-REC.
           05  LOG-TS                 PIC X(14).
           05  LOG-TEXT               PIC X(40).
           05  FILLER                 PIC X(6).
       WORKING-STORAGE SECTION.
       01  WS-LOG-STATUS          PIC X(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT LOG-FILE
           OPEN INPUT LOG-FILE
           PERFORM 9000-STATUS
           MOVE 'ORDER ORD00009 ACCEPTED' TO LOG-TEXT
           WRITE LOG-REC
           PERFORM 9000-STATUS
           REWRITE LOG-REC
           PERFORM 9000-STATUS
           CLOSE LOG-FILE
           CLOSE LOG-FILE
           PERFORM 9000-STATUS
           OPEN OUTPUT LOG-FILE
           READ LOG-FILE
           END-READ
           PERFORM 9000-STATUS
           CLOSE LOG-FILE
           DISPLAY 'AIXAFES BAD ' WS-BAD
           GOBACK.
       9000-STATUS.
           IF WS-LOG-STATUS = '41'
              DISPLAY 'FILE ALREADY OPEN'
              ADD 1 TO WS-BAD
           END-IF
           IF WS-LOG-STATUS = '42'
              DISPLAY 'FILE NOT OPEN'
              ADD 1 TO WS-BAD
           END-IF
           IF WS-LOG-STATUS = '47'
              DISPLAY 'READ ON OUTPUT FILE'
              ADD 1 TO WS-BAD
           END-IF
           IF WS-LOG-STATUS = '48'
              DISPLAY 'WRITE ON INPUT FILE'
              ADD 1 TO WS-BAD
           END-IF
           IF WS-LOG-STATUS = '49'
              DISPLAY 'REWRITE ON INPUT FILE'
              ADD 1 TO WS-BAD
           END-IF.
