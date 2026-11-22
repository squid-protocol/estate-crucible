       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAFOP.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAFOP - OPEN-TIME FILE STATUS OVER KSDS FILES.
      * FILE STATUS 05, 35 AND 39 ARE TESTED IN ONE PARAGRAPH EACH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT OPTIONAL CTL-FILE ASSIGN TO CTLKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS CTL-ID
               FILE STATUS IS WS-CTL-STATUS.
           SELECT CHK-FILE ASSIGN TO CHKKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS CHK-ID
               FILE STATUS IS WS-CHK-STATUS.
           SELECT ORD-FILE ASSIGN TO ORDKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS ORD-CUST
               FILE STATUS IS WS-ORD-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  CTL-FILE
           RECORDING MODE IS F.
       01  CTL-REC.
           05  CTL-ID                 PIC X(8).
           05  CTL-VAL                PIC X(32).
       FD  CHK-FILE
           RECORDING MODE IS F.
       01  CHK-REC.
           05  CHK-ID                 PIC X(8).
           05  CHK-VAL                PIC X(32).
       FD  ORD-FILE
           RECORDING MODE IS F.
       01  ORD-REC.
           05  ORD-ID                 PIC X(8).
           05  ORD-CUST               PIC X(8).
           05  FILLER                 PIC X(24).
       WORKING-STORAGE SECTION.
       01  WS-CTL-STATUS          PIC X(2).
       01  WS-CHK-STATUS          PIC X(2).
       01  WS-ORD-STATUS          PIC X(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT CTL-FILE
           PERFORM 1000-CTL-STATUS
           OPEN INPUT CHK-FILE
           PERFORM 2000-CHK-STATUS
           OPEN INPUT ORD-FILE
           PERFORM 3000-ORD-STATUS
           DISPLAY 'AIXAFOP BAD ' WS-BAD
           GOBACK.
       1000-CTL-STATUS.
           IF WS-CTL-STATUS = '05'
              DISPLAY 'CONTROL FILE ABSENT, TREATED AS EMPTY'
           ELSE
              IF WS-CTL-STATUS NOT = '00'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
       2000-CHK-STATUS.
           IF WS-CHK-STATUS = '35'
              DISPLAY 'CHECK FILE NOT AVAILABLE'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-CHK-STATUS NOT = '00'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
       3000-ORD-STATUS.
           IF WS-ORD-STATUS = '39'
              DISPLAY 'ORDER FILE ATTRIBUTE CONFLICT'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-ORD-STATUS NOT = '00'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
