       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQBRMPP.
       AUTHOR.       BRIDGE SYSTEMS.
      *------------------------------------------------------------
      * MQBRMPP - THE ORDER TRANSACTION THE IMS BRIDGE STARTS.
      * GU THE INPUT, ISRT THE REPLY TO THE IO PCB.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-GU                  PIC X(4) VALUE 'GU  '.
       01  WS-ISRT                PIC X(4) VALUE 'ISRT'.
       01  WS-IN-AREA.
           05  WS-IN-LL               PIC S9(4) COMP.
           05  WS-IN-ZZ               PIC S9(4) COMP.
           05  WS-IN-TRAN             PIC X(8).
           05  WS-IN-DATA             PIC X(12).
       01  WS-OUT-AREA.
           05  WS-OUT-LL              PIC S9(4) COMP VALUE 22.
           05  WS-OUT-ZZ              PIC S9(4) COMP VALUE 0.
           05  WS-OUT-TEXT PIC X(18) VALUE 'ORDER ACCEPTED    '.
       LINKAGE SECTION.
       01  IO-PCB.
           05  IO-LTERM               PIC X(8).
           05  IO-RSV                 PIC X(2).
           05  IO-STATUS              PIC X(2).
       PROCEDURE DIVISION USING IO-PCB.
       0000-MAIN.
           CALL 'CBLTDLI' USING WS-GU IO-PCB WS-IN-AREA
           IF IO-STATUS = SPACES
              PERFORM 1000-REPLY
           END-IF
           GOBACK.
       1000-REPLY.
           CALL 'CBLTDLI' USING WS-ISRT IO-PCB WS-OUT-AREA
           IF IO-STATUS NOT = SPACES
              DISPLAY 'MQBRMPP ISRT STATUS ' IO-STATUS
           END-IF.
