       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAKSD.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAKSD - ORDERS IN A KSDS WITH AN ALTERNATE KEY.
      * THE ALTERNATE INDEX IS REACHED BY PATH, DD ORDKSD1.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ORD-FILE ASSIGN TO ORDKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS ORD-ID
               ALTERNATE RECORD KEY IS ORD-CUST WITH DUPLICATES
               FILE STATUS IS WS-ORD-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  ORD-FILE
           RECORDING MODE IS F.
       01  ORD-REC.
           05  ORD-ID                 PIC X(8).
           05  ORD-CUST               PIC X(8).
           05  ORD-AMT                PIC 9(7).
           05  FILLER                 PIC X(17).
       WORKING-STORAGE SECTION.
       01  WS-ORD-STATUS          PIC X(2).
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-HITS                PIC 9(5) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O ORD-FILE
           IF WS-ORD-STATUS NOT = '00'
              DISPLAY 'AIXAKSD OPEN FAILED ' WS-ORD-STATUS
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-ADD
           PERFORM 2000-BROWSE
           PERFORM 3000-PROBE
           CLOSE ORD-FILE
           DISPLAY 'AIXAKSD HITS ' WS-HITS
           GOBACK.
       1000-ADD.
           MOVE 'ORD00001' TO ORD-ID
           MOVE 'CUST0001' TO ORD-CUST
           MOVE 100 TO ORD-AMT
           WRITE ORD-REC
           PERFORM 9000-STATUS
           MOVE 'ORD00002' TO ORD-ID
           WRITE ORD-REC
           PERFORM 9000-STATUS
           MOVE 'ORD00001' TO ORD-ID
           WRITE ORD-REC
           PERFORM 9000-STATUS.
       2000-BROWSE.
           MOVE 'CUST0001' TO ORD-CUST
           START ORD-FILE KEY IS EQUAL TO ORD-CUST
               INVALID KEY SET WS-EOF TO TRUE
           END-START
           PERFORM 2100-NEXT UNTIL WS-EOF.
       2100-NEXT.
           READ ORD-FILE NEXT RECORD
               AT END SET WS-EOF TO TRUE
           END-READ
           IF WS-ORD-STATUS > '02'
              SET WS-EOF TO TRUE
           END-IF
           IF NOT WS-EOF
              IF ORD-CUST = 'CUST0001'
                 ADD 1 TO WS-HITS
              ELSE
                 SET WS-EOF TO TRUE
              END-IF
           END-IF.
       3000-PROBE.
           MOVE 'ORD99999' TO ORD-ID
           READ ORD-FILE KEY IS ORD-ID
               INVALID KEY CONTINUE
           END-READ
           PERFORM 9000-STATUS.
       9000-STATUS.
           IF WS-ORD-STATUS = '23'
              DISPLAY 'ORDER NOT FOUND'
           ELSE
              IF WS-ORD-STATUS = '02'
                 DISPLAY 'DUPLICATE ALTERNATE KEY'
              ELSE
                 IF WS-ORD-STATUS = '22'
                    DISPLAY 'DUPLICATE PRIME KEY'
                 END-IF
              END-IF
           END-IF.
