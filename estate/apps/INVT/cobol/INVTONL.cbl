000100***************************************************************** INVTONL
000200*   INVTONL  -  ONLINE STOCK INQUIRY (TRANSACTION INVQ)         * INVTONL
000300*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 09/22/83     * INVTONL
000400***************************************************************** INVTONL
000500/                                                                 INVTONL
000600 IDENTIFICATION DIVISION.                                         INVTONL
000700 PROGRAM-ID.    INVTONL.                                          INVTONL
000800 AUTHOR.       D KOWALCZYK.                                       INVTONL
000900 INSTALLATION. MATERIALS CONTROL.                                 INVTONL
001000 DATE-WRITTEN. 09/22/83.                                          INVTONL
001100*------------------------------------------------------------     INVTONL
001200* INVTONL - STOCK INQUIRY, RECORD ADDRESSED BY BLL CELL.          INVTONL
001300*------------------------------------------------------------     INVTONL
001400 DATA DIVISION.                                                   INVTONL
001500 WORKING-STORAGE SECTION.                                         INVTONL
001600 01  WS-PART-KEY            PIC X(10).                            INVTONL
001700 LINKAGE SECTION.                                                 INVTONL
001800 01  BLL-CELLS.                                                   INVTONL
001900     02  FILLER                 PIC S9(8) COMP.                   INVTONL
002000     02  STK-BLL                PIC S9(8) COMP.                   INVTONL
002100     02  CWA-BLL                PIC S9(8) COMP.                   INVTONL
002200 01  STK-AREA.                                                    INVTONL
002300     COPY INVTREC.                                                INVTONL
002400 01  CWA-AREA.                                                    INVTONL
002500     02  CWA-PART-KEY           PIC X(10).                        INVTONL
002600     02  FILLER                 PIC X(70).                        INVTONL
002700 PROCEDURE DIVISION.                                              INVTONL
002800 0000-MAINLINE SECTION.                                           INVTONL
002900     EXEC CICS ADDRESS CWA(CWA-BLL)                               INVTONL
003000     END-EXEC                                                     INVTONL
003100     MOVE CWA-PART-KEY TO WS-PART-KEY                             INVTONL
003200     EXEC CICS READ DATASET('INVTMST') SET(STK-BLL)               INVTONL
003300               RIDFLD(WS-PART-KEY)                                INVTONL
003400     END-EXEC                                                     INVTONL
003500     EXEC CICS RETURN                                             INVTONL
003600     END-EXEC.                                                    INVTONL
