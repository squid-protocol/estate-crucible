       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSATRG.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSATRG - READ ONE TRIGGER MESSAGE FROM THE INITIATION QUEUE
      * AND NAME THE QUEUE THAT FIRED IT.
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
       01  WS-TM.
           COPY MQSTM.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSATRG CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.INITQ' TO MQS-OBJNAME
           MOVE 1 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSATRG OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-GET
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
       1000-GET.
           MOVE 3 TO MQS-GMO-OPTIONS
           MOVE 30000 TO MQS-GMO-WAITINT
           MOVE 684 TO WS-BUFLEN
           CALL 'MQGET'
               USING WS-HCONN WS-HOBJ WS-MD WS-GMO WS-BUFLEN WS-TM
               WS-DATALEN WS-COMPCODE WS-REASON
           IF WS-COMPCODE = 0
              DISPLAY 'MQSATRG TRIGGERED BY ' MQS-TM-QNAME
              DISPLAY 'MQSATRG PROCESS ' MQS-TM-PROCESS
           ELSE
              DISPLAY 'MQSATRG NO TRIGGER ' WS-REASON
              MOVE 4 TO RETURN-CODE
           END-IF.
