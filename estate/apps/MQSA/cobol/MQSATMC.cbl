       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSATMC.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSATMC - THE PROGRAM A TRIGGER MONITOR STARTS FOR ORDERS.IN.
      * THE MONITOR PASSES THE CHARACTER FORM OF THE TRIGGER (MQTMC2).
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
       01  WS-GMO.
           COPY MQSGMO.
       LINKAGE SECTION.
       01  LK-TMC.
           COPY MQSTMC2.
       PROCEDURE DIVISION USING LK-TMC.
       0000-MAIN.
           DISPLAY 'MQSATMC STARTED FOR ' MQS-TMC-QNAME
           MOVE MQS-TMC-QMGRNAME TO WS-QMGR
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSATMC CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE MQS-TMC-QNAME TO MQS-OBJNAME
           MOVE 1 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSATMC OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
