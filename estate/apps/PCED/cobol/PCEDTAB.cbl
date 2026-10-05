       IDENTIFICATION DIVISION.
       PROGRAM-ID.    PCEDTAB.
       AUTHOR.       PRICING TEAM. 	 
      *------------------------------------------------------------
      * PCEDTAB - PRICE TABLE LOAD. EDITED ON A PC.
      *------------------------------------------------------------  
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PRICES. 	 
           05	 WS-PRICE PIC S9(5)V99 COMP-3 OCCURS 10 TIMES.
       01  WS-I                   PIC S9(4) COMP VALUE 0.
       01  WS-TOTAL               PIC S9(7)V99 COMP-3 VALUE 0.  
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM	LOAD-TABLE 	 
           CALL	'PCEDLOW' USING WS-TOTAL
           GOBACK.
       LOAD-TABLE. 	 
           MOVE	1 TO WS-I
           PERFORM	ADD-PRICE UNTIL WS-I > 10.
       ADD-PRICE. 	 
           ADD	WS-PRICE (WS-I) TO WS-TOTAL
           ADD	1 TO WS-I.
