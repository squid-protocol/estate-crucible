       IDENTIFICATION DIVISION.
       PROGRAM-ID.    ORDVALV2.
       AUTHOR.       M OKAFOR.
       DATE-WRITTEN. 04/11/2016.
      *------------------------------------------------------------
      * ORDVALV2 - ORDVAL REWRITE (ORDER-NG). NOT IN PRODUCTION.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MAX-QTY             PIC S9(5) COMP-3 VALUE 5000.
       LINKAGE SECTION.
       01  LK-ORDER.
           COPY ORDREC.
       01  LK-PARM.
           COPY ORDPARM.
       PROCEDURE DIVISION USING LK-ORDER LK-PARM.
       0000-MAIN.
           MOVE ZERO TO PRM-RC
           PERFORM 1000-CHECK-QTY
           PERFORM 2000-CHECK-CHANNEL
           PERFORM 3000-CHECK-PRICE
           GOBACK.
       1000-CHECK-QTY.
           IF ORD-QTY > WS-MAX-QTY OR ORD-QTY NOT > ZERO
              SET ORD-REJECTED TO TRUE
              MOVE 8 TO PRM-RC
           END-IF.
       2000-CHECK-CHANNEL.
           IF ORD-CHANNEL = SPACES
              MOVE 'BT' TO ORD-CHANNEL
           END-IF.
       3000-CHECK-PRICE.
           IF ORD-PRICE < ZERO
              MOVE 12 TO PRM-RC
           END-IF.
