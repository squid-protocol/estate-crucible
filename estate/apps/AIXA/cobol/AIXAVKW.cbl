       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAVKW.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAVKW - TRIM A CUSTOMER NOTE IN PLACE.
      * A KSDS REWRITE MAY CHANGE THE LENGTH: FILE STATUS 00, NOT 44.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NOT-FILE ASSIGN TO NOTUPD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS NOT-ID
               FILE STATUS IS WS-NOT-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  NOT-FILE
           RECORDING MODE IS V
           RECORD IS VARYING IN SIZE FROM 30 TO 50 CHARACTERS
           DEPENDING ON WS-NOT-LEN.
       01  NOT-REC.
           05  NOT-ID                 PIC X(8).
           05  NOT-TEXT               PIC X(42).
       WORKING-STORAGE SECTION.
       01  WS-NOT-STATUS          PIC X(2).
       01  WS-NOT-LEN             PIC 9(3) VALUE ZERO.
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O NOT-FILE
           PERFORM 1000-SHRINK
           CLOSE NOT-FILE
           DISPLAY 'AIXAVKW BAD ' WS-BAD
           GOBACK.
       1000-SHRINK.
           READ NOT-FILE NEXT RECORD
               AT END CONTINUE
           END-READ
           MOVE 40 TO WS-NOT-LEN
           REWRITE NOT-REC
           IF WS-NOT-STATUS = '00'
              DISPLAY 'REWRITE CHANGED THE LENGTH'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
