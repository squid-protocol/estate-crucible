000100***************************************************************** INVTRLD
000200*   INVTRLD  -  ONLINE STOCK BROWSE, SERVICE RELOAD AFTER BLL   * INVTRLD
000300*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 11/08/83     * INVTRLD
000400***************************************************************** INVTRLD
000500/                                                                 INVTRLD
000600 IDENTIFICATION DIVISION.                                         INVTRLD
000700 PROGRAM-ID.    INVTRLD.                                          INVTRLD
000800 AUTHOR.       D KOWALCZYK.                                       INVTRLD
000900 INSTALLATION. MATERIALS CONTROL.                                 INVTRLD
001000 DATE-WRITTEN. 11/08/83.                                          INVTRLD
001100*------------------------------------------------------------     INVTRLD
001200* INVTRLD - STOCK RECORD BY BLL CELL, RELOADED.                   INVTRLD
001300*------------------------------------------------------------     INVTRLD
001400 DATA DIVISION.                                                   INVTRLD
001500 WORKING-STORAGE SECTION.                                         INVTRLD
001600 01  WS-PART-KEY            PIC X(10).                            INVTRLD
001700 01  WS-BUMP                PIC S9(8) COMP VALUE 4096.            INVTRLD
001800 LINKAGE SECTION.                                                 INVTRLD
001900 01  PARMLIST.                                                    INVTRLD
002000     02  PARM-BLL               PIC S9(8) COMP.                   INVTRLD
002100 01  BLL-CELLS.                                                   INVTRLD
002200     02  FILLER                 PIC S9(8) COMP.                   INVTRLD
002300     02  STK-BLL                PIC S9(8) COMP.                   INVTRLD
002400 01  STK-AREA.                                                    INVTRLD
002500     COPY INVTREC.                                                INVTRLD
002600 PROCEDURE DIVISION.                                              INVTRLD
002700 0000-MAINLINE SECTION.                                           INVTRLD
002800     SERVICE RELOAD PARMLIST                                      INVTRLD
002900     MOVE SPACES TO WS-PART-KEY                                   INVTRLD
003000     EXEC CICS READ DATASET('INVTMST') SET(STK-BLL)               INVTRLD
003100               RIDFLD(WS-PART-KEY)                                INVTRLD
003200     END-EXEC                                                     INVTRLD
003300     ADD WS-BUMP TO STK-BLL                                       INVTRLD
003400     SERVICE RELOAD STK-AREA                                      INVTRLD
003500     EXEC CICS RETURN                                             INVTRLD
003600     END-EXEC.                                                    INVTRLD
