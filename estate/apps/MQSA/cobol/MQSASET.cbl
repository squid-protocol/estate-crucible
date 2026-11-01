       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSASET.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSASET - INHIBIT PUTS ON THE ORDER QUEUE, ONE MQSET.
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
       01  WS-SEL-COUNT           PIC S9(9) COMP VALUE 1.
       01  WS-SEL-BLOCK.
           05  WS-SEL-INHIBIT         PIC S9(9) COMP VALUE 6.
       01  WS-INT-COUNT           PIC S9(9) COMP VALUE 1.
       01  WS-INT-BLOCK.
           05  WS-INHIBIT-PUT         PIC S9(9) COMP VALUE 1.
       01  WS-CHAR-LEN            PIC S9(9) COMP VALUE 0.
       01  WS-CHAR-ATTRS          PIC X(8).
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSASET CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.IN' TO MQS-OBJNAME
           MOVE 64 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSASET OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL 'MQSET'
               USING WS-HCONN WS-HOBJ WS-SEL-COUNT WS-SEL-BLOCK
               WS-INT-COUNT WS-INT-BLOCK WS-CHAR-LEN WS-CHAR-ATTRS
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSASET SET FAILED ' WS-REASON
           END-IF
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
