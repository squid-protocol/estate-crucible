       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSAINQ.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSAINQ - DEPTH OF THE ORDER QUEUE, ONE MQINQ.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-QMGR                PIC X(48) VALUE 'QM01'.
       01  WS-HCONN               PIC S9(9) COMP VALUE 0.
       01  WS-HOBJ                PIC S9(9) COMP VALUE 0.
       01  WS-COMPCODE            PIC S9(9) COMP VALUE 0.
       01  WS-REASON              PIC S9(9) COMP VALUE 0.
       01  WS-OO-OPTIONS          PIC S9(9) COMP VALUE 0.
       01  WS-CO-OPTIONS          PIC S9(9) COMP VALUE 0.
       01  WS-BUFLEN              PIC S9(9) COMP VALUE 80.
       01  WS-DATALEN             PIC S9(9) COMP VALUE 0.
       01  WS-BUF                 PIC X(80).
       01  WS-OD.
           COPY MQSOD.
       01  WS-SEL-COUNT           PIC S9(9) COMP VALUE 2.
       01  WS-SEL-BLOCK.
           05  WS-SEL-DEPTH           PIC S9(9) COMP VALUE 3.
           05  WS-SEL-MAX             PIC S9(9) COMP VALUE 15.
       01  WS-INT-COUNT           PIC S9(9) COMP VALUE 2.
       01  WS-INT-BLOCK.
           05  WS-DEPTH               PIC S9(9) COMP VALUE 0.
           05  WS-MAXDEPTH            PIC S9(9) COMP VALUE 0.
       01  WS-CHAR-LEN            PIC S9(9) COMP VALUE 0.
       01  WS-CHAR-ATTRS          PIC X(8).
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSAINQ CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.IN' TO MQS-OBJNAME
           MOVE 32 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSAINQ OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL 'MQINQ'
               USING WS-HCONN WS-HOBJ WS-SEL-COUNT WS-SEL-BLOCK
               WS-INT-COUNT WS-INT-BLOCK WS-CHAR-LEN WS-CHAR-ATTRS
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE = 0
              DISPLAY 'MQSAINQ DEPTH ' WS-DEPTH ' OF ' WS-MAXDEPTH
           END-IF
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
