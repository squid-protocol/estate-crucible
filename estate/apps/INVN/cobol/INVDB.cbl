       IDENTIFICATION DIVISION.
       PROGRAM-ID.    INVDB.
       AUTHOR.       INVENTORY.
      *------------------------------------------------------------
      * INVDB - INVENTORY DB2 ACCESS. LINKED FROM INVUPD.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL INCLUDE DCLINVT END-EXEC.
       01  WS-SQLCODE             PIC -9(9).
       LINKAGE SECTION.
       01  DFHCOMMAREA.
           COPY INVCOMM.
       PROCEDURE DIVISION.
       0000-MAIN.
           MOVE IC-ITEM-ID TO ITEM-ID
           EXEC SQL
               UPDATE PROD.INVENTORY
                  SET ON_HAND = ON_HAND + :IC-QTY
                WHERE ITEM_ID = :ITEM-ID
           END-EXEC
           IF SQLCODE NOT = 0
              MOVE SQLCODE TO WS-SQLCODE
              MOVE 8 TO IC-RC
           END-IF
           EXEC CICS RETURN
           END-EXEC.
