       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSABKO.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSABKO - MQ-ONLY BACK-OUT: PUT UNDER SYNCPOINT, THEN MQBACK.
      * NO OTHER RESOURCE MANAGER IS TOUCHED: MQBACK IS ENOUGH.
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
       01  WS-MD.
           COPY MQSMD.
       01  WS-OD.
           COPY MQSOD.
       01  WS-PMO.
           COPY MQSPMO.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSABKO CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.IN' TO MQS-OBJNAME
           MOVE 16 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSABKO OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 2 TO MQS-PMO-OPTIONS
           MOVE 'ORDER ORD00004 DRAFT' TO WS-BUF
           CALL 'MQPUT'
               USING WS-HCONN WS-HOBJ WS-MD WS-PMO WS-BUFLEN WS-BUF
               WS-COMPCODE WS-REASON
           DISPLAY 'MQSABKO DRAFT REJECTED, BACKING OUT'
           CALL 'MQBACK' USING WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSABKO BACKOUT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
