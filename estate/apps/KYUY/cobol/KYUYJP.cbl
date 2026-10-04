       IDENTIFICATION DIVISION.
       PROGRAM-ID.    給与計算.
      *------------------------------------------------------------
      * KYUYJP - 給与計算 (REHOSTED, UTF-8)
      *------------------------------------------------------------
       DATA　DIVISION.
       WORKING-STORAGE SECTION.
       01　Ｆ０２　PIC　X.
       01  社員コード                  PIC X(6).
       01  X項目                    PIC X(4).
       01  FIXED_FLD              PIC X(2).
       01  ＴＥＳＴ−ＤＡＴＡ１             PIC X(2).
       01  ＴＥＳＴ−ＲＥＣＯＲＤ１           PIC X(2).
       01  ＴＥＳＴ－ＤＡＴＡ２             PIC X(2).
       01  WS-KYUY.
           COPY　KYUYCPY.
       PROCEDURE DIVISION.
       主処理 SECTION.
       開始.
           MOVE '000001' TO 社員コード
           MOVE SPACES TO ＴＥＳＴ−ＤＡＴＡ１
           MOVE 'AB' TO ＴＥＳＴ−ＲＥＣＯＲＤ１
           PERFORM Ｓ−初期化
           GOBACK.
       Ｓ−初期化 SECTION.
       初期化１.
           MOVE SPACE TO X項目
           MOVE 'Z' TO Ｆ０２.
