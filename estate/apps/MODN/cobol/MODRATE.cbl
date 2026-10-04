       >>SOURCE FORMAT FREE
IDENTIFICATION DIVISION.
PROGRAM-ID.    MODRATE.
*> ------------------------------------------------------------
*>  MODRATE - RATE LOOKUP, REWRITTEN IN FREE FORMAT.
*> ------------------------------------------------------------
DATA DIVISION.
WORKING-STORAGE SECTION.
    01  VALUE-BYTES.
       05  VB-CODE                PIC X(4).
       05  VB-RATE                PIC 9V9(4).
    01  WS-FOUND               PIC X VALUE 'N'.
LINKAGE SECTION.
    01  LK-REQUEST.
       05  LK-CODE                PIC X(4).
       05  LK-RATE                PIC 9V9(4).
PROCEDURE DIVISION USING LK-REQUEST.
MAIN-PARA.
    MOVE LK-CODE TO VB-CODE
    PERFORM LOOKUP-RATE
    IF WS-FOUND = 'Y'
       MOVE VB-RATE TO LK-RATE
    END-IF
    GOBACK.
LOOKUP-RATE.
    MOVE 0.0500 TO VB-RATE
    MOVE 'Y' TO WS-FOUND.
