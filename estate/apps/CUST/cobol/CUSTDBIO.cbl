       IDENTIFICATION DIVISION.
       PROGRAM-ID.    CUSTDBIO.
       AUTHOR.       CUSTOMER SYSTEMS.
      *------------------------------------------------------------
      * CUSTDBIO - CUSTOMER DB2 ACCESS. LINKED FROM CUSTINQ.
      * BALANCE REFRESH AND AUDIT ARE DB2 STORED PROCEDURES.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL INCLUDE DCLCUST END-EXEC.
       01  WS-SQLCODE             PIC -9(9).
       01  WS-BAL-IND             PIC S9(4) COMP.
       LINKAGE SECTION.
       01  DFHCOMMAREA.
           COPY CUSTCOMM.
       PROCEDURE DIVISION.
       0000-MAIN.
           MOVE CA-CUST-ID TO CUST-ID
           PERFORM 1000-SELECT-CUSTOMER
           IF SQLCODE = 0
              PERFORM 2000-REFRESH-BALANCE
           END-IF
           EXEC CICS RETURN
           END-EXEC.
       1000-SELECT-CUSTOMER.
           EXEC SQL
               SELECT CUST_NAME, CUST_BAL
                 INTO :CUST-NAME, :CUST-BAL :WS-BAL-IND
                 FROM PROD.CUSTOMER
                WHERE CUST_ID = :CUST-ID
           END-EXEC
           IF SQLCODE NOT = 0
              MOVE SQLCODE TO WS-SQLCODE
              MOVE 8 TO CA-RETURN-CODE
           END-IF.
       2000-REFRESH-BALANCE.
           EXEC SQL
               CALL PRODPROC.CUSTBAL
                    (:CUST-ID, :CUST-BAL)
           END-EXEC
           EXEC SQL CALL CUSTAUDT END-EXEC
           EXEC SQL
               UPDATE PROD.CUSTOMER
                  SET CUST_UPD_DATE = CURRENT DATE
                WHERE CUST_ID = :CUST-ID
           END-EXEC.
