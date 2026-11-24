       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSASUB.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSASUB - SUBSCRIBE TO THE ORDER TOPIC WITH A MANAGED QUEUE,
      * READ ONE PUBLICATION, THEN CLOSE THE QUEUE AND THE SUBSCRIPTION.
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
       01  WS-GMO.
           COPY MQSGMO.
       01  WS-SD.
           COPY MQSSD.
       01  WS-HSUB                PIC S9(9) COMP VALUE 0.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSASUB CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS/NEW' TO MQS-SD-TOPICSTR
           MOVE 34 TO MQS-SD-OPTIONS
           CALL 'MQSUB'
               USING WS-HCONN WS-SD WS-HOBJ WS-HSUB WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSASUB SUBSCRIBE FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-GET
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HSUB WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
       1000-GET.
           MOVE 1 TO MQS-GMO-OPTIONS
           MOVE 5000 TO MQS-GMO-WAITINT
           CALL 'MQGET'
               USING WS-HCONN WS-HOBJ WS-MD WS-GMO WS-BUFLEN WS-BUF
               WS-DATALEN WS-COMPCODE WS-REASON
           IF WS-COMPCODE = 0
              DISPLAY 'MQSASUB PUBLICATION ' WS-BUF
           ELSE
              DISPLAY 'MQSASUB NO PUBLICATION ' WS-REASON
              MOVE 4 TO RETURN-CODE
           END-IF.
