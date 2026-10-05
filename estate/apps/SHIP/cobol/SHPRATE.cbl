       IDENTIFICATION DIVISION.
       PROGRAM-ID.    SHPRATE.
       AUTHOR.       LOGISTICS IT.
      *------------------------------------------------------------
      * SHPRATE - CARRIER RATE LOOKUP (LINKED FROM SHPINQ).
      *------------------------------------------------------------
       DATA DIVISION.
       LINKAGE SECTION.
       01  DFHCOMMAREA.
           COPY SHPCOMM.
       PROCEDURE DIVISION.
       0000-MAIN.
           IF CA-CARRIER = SPACES
              MOVE 'GROUND' TO CA-CARRIER
           END-IF
           EXEC CICS RETURN
           END-EXEC.
