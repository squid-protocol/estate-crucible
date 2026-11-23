       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAVAR.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAVAR - VARIABLE-LENGTH CUSTOMER NOTES IN A KSDS.
      * FILE STATUS 44 ON WRITE, 04 ON READ: THE VARYING BOUNDS.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NOT-FILE ASSIGN TO NOTKSD
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
           PERFORM 1000-TOO-LONG
           PERFORM 2000-TOO-SHORT
           PERFORM 3000-ODD-READ
           CLOSE NOT-FILE
           DISPLAY 'AIXAVAR BAD ' WS-BAD
           GOBACK.
       1000-TOO-LONG.
           MOVE 'NOT00010' TO NOT-ID
           MOVE 60 TO WS-NOT-LEN
           WRITE NOT-REC
           IF WS-NOT-STATUS = '44'
              DISPLAY 'RECORD LARGER THAN THE LARGEST'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
       2000-TOO-SHORT.
           MOVE 'NOT00011' TO NOT-ID
           MOVE 10 TO WS-NOT-LEN
           WRITE NOT-REC
           IF WS-NOT-STATUS = '44'
              DISPLAY 'RECORD SMALLER THAN THE SMALLEST'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
       3000-ODD-READ.
           READ NOT-FILE NEXT RECORD
               AT END CONTINUE
           END-READ
           IF WS-NOT-STATUS = '04'
              DISPLAY 'RECORD LENGTH OUTSIDE THE FD'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
