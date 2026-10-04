       IDENTIFICATION DIVISION.
       PROGRAM-ID.    INVUPD.
       AUTHOR.       INVENTORY.
      *------------------------------------------------------------
      * INVUPD - ADJUST ON-HAND QUANTITY (TRANSACTION IUPD).
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-INV-AREA.
           COPY INVCOMM.
           COPY INVMSG.
       01  WS-ITEM-REC.
           COPY INVITEM.
       01  WS-RESP                PIC S9(8) COMP.
       01  WS-TSQ-NAME            PIC X(8) VALUE 'INVAUDIT'.
       LINKAGE SECTION.
       01  DFHCOMMAREA.
           COPY INVCOMM.
       PROCEDURE DIVISION.
       0000-MAIN.
           MOVE DFHCOMMAREA TO WS-INV-AREA
           PERFORM 1000-READ-ITEM
           IF WS-RESP = 0
              PERFORM 2000-ADJUST
           END-IF
           PERFORM 3000-AUDIT
           EXEC CICS RETURN
           END-EXEC.
       1000-READ-ITEM.
           EXEC CICS READ FILE('INVFILE') INTO(WS-ITEM-REC)
                     RIDFLD(IC-ITEM-ID OF WS-INV-AREA)
                     UPDATE RESP(WS-RESP)
           END-EXEC.
       2000-ADJUST.
           ADD IC-QTY OF WS-INV-AREA TO INV-WH1-ONHAND
      *    CALL 'OLDINVAD' USING WS-INV-AREA
      *    PERFORM 2500-OLD-REORDER
           EXEC CICS REWRITE FILE('INVFILE') FROM(WS-ITEM-REC)
           END-EXEC
           EXEC CICS LINK PROGRAM('INVDB') COMMAREA(WS-INV-AREA)
           END-EXEC.
       3000-AUDIT.
           MOVE IC-ITEM-ID OF WS-INV-AREA TO INV-MSG-CODE
           EXEC CICS WRITEQ TS QUEUE(WS-TSQ-NAME) FROM(INV-MSG-REC)
           END-EXEC.
