       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAFSQ.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAFSQ - SEQUENTIAL LOAD AND UPDATE OF THE ORDER KSDS.
      * FILE STATUS 21, 43 AND 46 ARE TESTED IN ONE PARAGRAPH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SEQ-FILE ASSIGN TO ORDSEQ
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS SEQ-ID
               FILE STATUS IS WS-SEQ-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  SEQ-FILE
           RECORDING MODE IS F.
       01  SEQ-REC.
           05  SEQ-ID                 PIC X(8).
           05  SEQ-CUST               PIC X(8).
           05  FILLER                 PIC X(24).
       WORKING-STORAGE SECTION.
       01  WS-SEQ-STATUS          PIC X(2).
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN OUTPUT SEQ-FILE
           PERFORM 1000-LOAD
           CLOSE SEQ-FILE
           OPEN I-O SEQ-FILE
           PERFORM 2000-UPDATE
           CLOSE SEQ-FILE
           DISPLAY 'AIXAFSQ BAD ' WS-BAD
           GOBACK.
       1000-LOAD.
           MOVE 'ORD00002' TO SEQ-ID
           MOVE 'CUST0002' TO SEQ-CUST
           WRITE SEQ-REC
           PERFORM 9000-STATUS
           MOVE 'ORD00001' TO SEQ-ID
           WRITE SEQ-REC
           PERFORM 9000-STATUS.
       2000-UPDATE.
           MOVE 'CUST0009' TO SEQ-CUST
           REWRITE SEQ-REC
           PERFORM 9000-STATUS
           READ SEQ-FILE NEXT RECORD
               AT END SET WS-EOF TO TRUE
           END-READ
           PERFORM 2100-NEXT UNTIL WS-EOF
           READ SEQ-FILE NEXT RECORD
               AT END SET WS-EOF TO TRUE
           END-READ
           PERFORM 9000-STATUS.
       2100-NEXT.
           READ SEQ-FILE NEXT RECORD
               AT END SET WS-EOF TO TRUE
           END-READ.
       9000-STATUS.
           IF WS-SEQ-STATUS = '21'
              DISPLAY 'KEY OUT OF SEQUENCE'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-SEQ-STATUS = '43'
                 DISPLAY 'REWRITE WITHOUT READ'
                 ADD 1 TO WS-BAD
              ELSE
                 IF WS-SEQ-STATUS = '46'
                    DISPLAY 'READ PAST END'
                    ADD 1 TO WS-BAD
                 END-IF
              END-IF
           END-IF.
