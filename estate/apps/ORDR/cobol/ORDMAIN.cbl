000100 IDENTIFICATION DIVISION.                                         ORDMAIN
000200 PROGRAM-ID.    ORDMAIN.                                          ORDMAIN
000300 AUTHOR.       D PRZYBYL.                                         ORDMAIN
000400 INSTALLATION. ORDER SYSTEMS.                                     ORDMAIN
000500 DATE-WRITTEN. 09/30/94.                                          ORDMAIN
000600*------------------------------------------------------------     ORDMAIN
000700* ORDMAIN - NIGHTLY ORDER EDIT AND PRICING. JOB ORDNITE.          ORDMAIN
000800*------------------------------------------------------------     ORDMAIN
000900 ENVIRONMENT DIVISION.                                            ORDMAIN
001000 INPUT-OUTPUT SECTION.                                            ORDMAIN
001100 FILE-CONTROL.                                                    ORDMAIN
001200     SELECT ORDER-FILE ASSIGN TO ORDIN                            ORDMAIN
001300         ORGANIZATION IS SEQUENTIAL                               ORDMAIN
001400         FILE STATUS IS WS-ORD-STATUS.                            ORDMAIN
001500 DATA DIVISION.                                                   ORDMAIN
001600 FILE SECTION.                                                    ORDMAIN
001700 FD  ORDER-FILE                                                   ORDMAIN
001800     RECORDING MODE IS F.                                         ORDMAIN
001900 01  ORD-IN-REC             PIC X(41).                            ORDMAIN
002000 WORKING-STORAGE SECTION.                                         ORDMAIN
002100 01  WS-ORD-STATUS          PIC X(2).                             ORDMAIN
002200 01  WS-EOF-FLAG            PIC X VALUE 'N'.                      ORDMAIN
002300     88  WS-EOF                 VALUE 'Y'.                        ORDMAIN
002400 01  WS-ORDER.                                                    ORDMAIN
002500     COPY ORDREC.                                                 ORDMAIN
002600 01  WS-PARM.                                                     ORDMAIN
002700     COPY ORDPARM.                                                ORDMAIN
002800 01  WS-PRICE-PARM.                                               ORDMAIN
002900     COPY ORDPRICE.                                               ORDMAIN
003000 PROCEDURE DIVISION.                                              ORDMAIN
003100 0000-MAIN.                                                       ORDMAIN
003200     OPEN INPUT ORDER-FILE                                        ORDMAIN
003300     PERFORM 1000-NEXT-ORDER UNTIL WS-EOF                         ORDMAIN
003400     CLOSE ORDER-FILE                                             ORDMAIN
003500*    PERFORM 9000-OLD-RECOVERY                                    ORDMAIN
003600     GOBACK.                                                      ORDMAIN
003700 1000-NEXT-ORDER.                                                 ORDMAIN
003800     READ ORDER-FILE INTO WS-ORDER                                ORDMAIN
003900        AT END                                                    ORDMAIN
004000           SET WS-EOF TO TRUE                                     ORDMAIN
004100        NOT AT END                                                ORDMAIN
004200           CALL 'ORDVAL' USING WS-ORDER WS-PARM                   ORDMAIN
004300           CALL 'ORDPRICE' USING WS-ORDER                         ORDMAIN
004400     END-READ.                                                    ORDMAIN
004500 9000-OLD-RECOVERY.                                               ORDMAIN
004600     DISPLAY 'ORDMAIN RESTART FROM CHECKPOINT'                    ORDMAIN
004700     MOVE 'Y' TO WS-EOF-FLAG.                                     ORDMAIN
