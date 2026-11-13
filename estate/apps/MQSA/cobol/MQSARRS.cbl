       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSARRS.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSARRS - PUT ONE ORDER AND COMMIT THROUGH RRS.
      * LINKED WITH CSQBRSTB: THE SYNCPOINT IS SRRCMIT / SRRBACK.
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
       01  WS-RRS-RC              PIC S9(9) COMP VALUE 0.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSARRS CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.IN' TO MQS-OBJNAME
           MOVE 16 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSARRS OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 2 TO MQS-PMO-OPTIONS
           MOVE 'ORDER ORD00003 75' TO WS-BUF
           CALL 'MQPUT'
               USING WS-HCONN WS-HOBJ WS-MD WS-PMO WS-BUFLEN WS-BUF
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE = 0
              CALL 'SRRCMIT' USING WS-RRS-RC
           ELSE
              CALL 'SRRBACK' USING WS-RRS-RC
           END-IF
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
