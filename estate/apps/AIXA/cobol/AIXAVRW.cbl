       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAVRW.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAVRW - TRIM A LOG RECORD IN PLACE.
      * FILE STATUS 44: AN ESDS REWRITE CANNOT CHANGE THE LENGTH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOG-FILE ASSIGN TO LOGUPD
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-LOG-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  LOG-FILE
           RECORDING MODE IS V
           RECORD IS VARYING IN SIZE FROM 40 TO 60 CHARACTERS
           DEPENDING ON WS-LOG-LEN.
       01  LOG-REC.
           05  LOG-TS                 PIC X(14).
           05  LOG-TEXT               PIC X(40).
           05  FILLER                 PIC X(6).
       WORKING-STORAGE SECTION.
       01  WS-LOG-STATUS          PIC X(2).
       01  WS-LOG-LEN             PIC 9(3) VALUE ZERO.
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O LOG-FILE
           PERFORM 1000-SHRINK
           CLOSE LOG-FILE
           DISPLAY 'AIXAVRW BAD ' WS-BAD
           GOBACK.
       1000-SHRINK.
           READ LOG-FILE NEXT RECORD
               AT END CONTINUE
           END-READ
           MOVE 50 TO WS-LOG-LEN
           REWRITE LOG-REC
           IF WS-LOG-STATUS = '44'
              DISPLAY 'REWRITE CHANGES THE LENGTH'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
