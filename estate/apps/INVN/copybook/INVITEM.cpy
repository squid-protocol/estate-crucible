      * INVITEM  - INVENTORY ITEM MASTER (DATA ONLY)
           05  INV-ITEM.
           10  INV-ITEM-ID            PIC X(12).
           10  INV-DESC               PIC X(40).
           10  INV-UOM                PIC X(4).
           10  INV-WH1.
               15  INV-WH1-ID             PIC X(4).
               15  INV-WH1-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH1-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH1-REORDER        PIC S9(7) COMP-3.
               15  INV-WH1-BIN            PIC X(8).
               15  INV-WH1-LAST-CNT       PIC 9(8).
               15  INV-WH1-FLAG           PIC X.
                   88  INV-WH1-ACTIVE         VALUE 'A'.
           10  INV-WH2.
               15  INV-WH2-ID             PIC X(4).
               15  INV-WH2-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH2-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH2-REORDER        PIC S9(7) COMP-3.
               15  INV-WH2-BIN            PIC X(8).
               15  INV-WH2-LAST-CNT       PIC 9(8).
               15  INV-WH2-FLAG           PIC X.
                   88  INV-WH2-ACTIVE         VALUE 'A'.
           10  INV-WH3.
               15  INV-WH3-ID             PIC X(4).
               15  INV-WH3-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH3-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH3-REORDER        PIC S9(7) COMP-3.
               15  INV-WH3-BIN            PIC X(8).
               15  INV-WH3-LAST-CNT       PIC 9(8).
               15  INV-WH3-FLAG           PIC X.
                   88  INV-WH3-ACTIVE         VALUE 'A'.
           10  INV-WH4.
               15  INV-WH4-ID             PIC X(4).
               15  INV-WH4-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH4-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH4-REORDER        PIC S9(7) COMP-3.
               15  INV-WH4-BIN            PIC X(8).
               15  INV-WH4-LAST-CNT       PIC 9(8).
               15  INV-WH4-FLAG           PIC X.
                   88  INV-WH4-ACTIVE         VALUE 'A'.
           10  INV-WH5.
               15  INV-WH5-ID             PIC X(4).
               15  INV-WH5-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH5-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH5-REORDER        PIC S9(7) COMP-3.
               15  INV-WH5-BIN            PIC X(8).
               15  INV-WH5-LAST-CNT       PIC 9(8).
               15  INV-WH5-FLAG           PIC X.
                   88  INV-WH5-ACTIVE         VALUE 'A'.
           10  INV-WH6.
               15  INV-WH6-ID             PIC X(4).
               15  INV-WH6-ONHAND         PIC S9(7) COMP-3.
               15  INV-WH6-ALLOC          PIC S9(7) COMP-3.
               15  INV-WH6-REORDER        PIC S9(7) COMP-3.
               15  INV-WH6-BIN            PIC X(8).
               15  INV-WH6-LAST-CNT       PIC 9(8).
               15  INV-WH6-FLAG           PIC X.
                   88  INV-WH6-ACTIVE         VALUE 'A'.
           10  INV-COST               PIC S9(9)V9(4) COMP-3.
           10  INV-PRICE              PIC S9(9)V99 COMP-3.
