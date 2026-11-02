000100***************************************************************** INVTLRG
000200*   INVTLRG  -  ONLINE STOCK DETAIL, LONG RECORD BY BLL CELLS   * INVTLRG
000300*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 02/21/84     * INVTLRG
000400***************************************************************** INVTLRG
000500/                                                                 INVTLRG
000600 IDENTIFICATION DIVISION.                                         INVTLRG
000700 PROGRAM-ID.    INVTLRG.                                          INVTLRG
000800 AUTHOR.       D KOWALCZYK.                                       INVTLRG
000900 INSTALLATION. MATERIALS CONTROL.                                 INVTLRG
001000 DATE-WRITTEN. 02/21/84.                                          INVTLRG
001100*------------------------------------------------------------     INVTLRG
001200* INVTLRG - 5400 BYTE DETAIL RECORD, TWO BLL CELLS.               INVTLRG
001300*------------------------------------------------------------     INVTLRG
001400 DATA DIVISION.                                                   INVTLRG
001500 WORKING-STORAGE SECTION.                                         INVTLRG
001600 01  WS-PART-KEY            PIC X(10).                            INVTLRG
001700 LINKAGE SECTION.                                                 INVTLRG
001800 01  BLL-CELLS.                                                   INVTLRG
001900     02  FILLER                 PIC S9(8) COMP.                   INVTLRG
002000     02  LONG-BLL               PIC S9(8) COMP.                   INVTLRG
002100     02  LONG-BLL2              PIC S9(8) COMP.                   INVTLRG
002200     02  FULL-BLL               PIC S9(8) COMP.                   INVTLRG
002300 01  STK-LONG.                                                    INVTLRG
002400     02  LNG-HEADER             PIC X(4000).                      INVTLRG
002500     02  LNG-DETAIL             PIC X(1000).                      INVTLRG
002600     02  LNG-TRAILER            PIC X(400).                       INVTLRG
002700 01  STK-FULL.                                                    INVTLRG
002800     02  FUL-BODY               PIC X(4096).                      INVTLRG
002900 PROCEDURE DIVISION.                                              INVTLRG
003000 0000-MAINLINE SECTION.                                           INVTLRG
003100     MOVE SPACES TO WS-PART-KEY                                   INVTLRG
003200     EXEC CICS READ DATASET('INVTDTL') SET(LONG-BLL)              INVTLRG
003300               RIDFLD(WS-PART-KEY)                                INVTLRG
003400     END-EXEC                                                     INVTLRG
003500     ADD 4096 LONG-BLL GIVING LONG-BLL2.                          INVTLRG
003600     SERVICE RELOAD STK-LONG.                                     INVTLRG
003700     EXEC CICS READ DATASET('INVTFUL') SET(FULL-BLL)              INVTLRG
003800               RIDFLD(WS-PART-KEY)                                INVTLRG
003900     END-EXEC                                                     INVTLRG
004000     SERVICE RELOAD STK-FULL.                                     INVTLRG
004100     EXEC CICS RETURN                                             INVTLRG
004200     END-EXEC.                                                    INVTLRG
