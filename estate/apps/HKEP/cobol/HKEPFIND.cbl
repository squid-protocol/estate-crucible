       IDENTIFICATION DIVISION.
       PROGRAM-ID.    HKEPFIND.
       AUTHOR.       KEEP SYSTEMS.
      *------------------------------------------------------------
      * HKEPFIND - GET ONE KEEP BY KEY WITH A QUALIFIED SSA.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-GU                  PIC X(4) VALUE 'GU  '.
       01  WS-IO-AREA             PIC X(80).
       01  SSA-KEEP.
           05  SSA-SEGNAME            PIC X(8) VALUE 'KEEP    '.
           05  SSA-LPAREN             PIC X VALUE '('.
           05  SSA-FLDNAME            PIC X(8) VALUE 'KEEPKEY '.
           05  SSA-OPER               PIC XX VALUE ' ='.
           05  SSA-FLDVAL             PIC X(8) VALUE 'K0001234'.
           05  SSA-RPAREN             PIC X VALUE ')'.
       LINKAGE SECTION.
       01  IO-PCB.
           05  IO-LTERM               PIC X(8).
           05  IO-RSV                 PIC X(2).
           05  IO-STATUS              PIC X(2).
       01  DB-PCB.
           05  DB-DBD                 PIC X(8).
           05  DB-LEVEL               PIC X(2).
           05  DB-STATUS              PIC X(2).
       PROCEDURE DIVISION USING IO-PCB DB-PCB.
       0000-MAIN.
           CALL 'CBLTDLI' USING WS-GU DB-PCB WS-IO-AREA SSA-KEEP
           IF DB-STATUS = SPACES
              DISPLAY 'KEEP FOUND'
           END-IF
           GOBACK.
