"""KYUY -- Japanese payroll. The same estate in four encodings, as Japanese estates are:
the z/OS program in EBCDIC cp930 (Katakana-Kanji) as 80-byte records with Shift-Out /
Shift-In around every DBCS run, a copybook in cp939 (Latin-Kanji) with NEL line ends, a PC
download in Shift-JIS, and a program rehosted on Linux in UTF-8 (opensourcecobol4j style)
whose names mix Japanese, full-width forms and the full-width space.

Planted: H-0038 (D030), H-0040 (D029), H-0041 (D031), H-0042 (DBCS literals and shift
codes), H-0046 (Shift-JIS)."""

from ..codepages import RAW_SI, RAW_SO
from ..data import CP, C, I
from ..stmt import goback, para, perform, raw, section

H38, H40, H41, H42, H46 = "H-0038", "H-0040", "H-0041", "H-0042", "H-0046"

COPYBOOKS = [
    {"member": "SHAINREC", "header": [" SHAINREC - 社員レコード (CP939)"], "horror": H42,
     "encoding": ("cp939", "nel"),
     "items": [I(1, "社員レコード", kids=[I(5, "社員番号", "X(6)"), I(5, "社員名", "G(10)"),
                                       I(5, "給与額", "S9(7)", "COMP-3")])]},
    # a UTF-8 copybook with a byte-order mark, copied with a full-width space after COPY
    {"member": "KYUYCPY", "header": [" KYUYCPY - 共通項目 (UTF-8, BOM)"], "horror": H38,
     "encoding": ("utf-8-sig", "lf"),
     "items": [I(5, "共通コード", "X(4)"), I(5, "共通日付", "X(8)")]},
]

KYUYO01 = {
    "member": "KYUYO01",
    "program_id": "KYUYO01",
    "member_horror": H42,
    "compile": "ibm-only",
    "compile_reason": "PIC G / G'...' (DBCS, USAGE DISPLAY-1): GnuCOBOL 3.1 has no DBCS category",
    "compile_check": ("pic-g-to-n", "PIC G and G'...' become PIC N and N'...' for the check (same 2-byte width)"),
    "remarks": ["KYUYO01 - 給与計算 (CP930)", "旧仕様:" + RAW_SO + "漢字",
                "入れ子:" + RAW_SO + RAW_SO + "漢" + RAW_SI],
    "ws": [
        I(1, "処理件数", "9(5)", "COMP-3", value="0"),
        I(1, "見出し", "X(20)", value="'給与明細ABC'"),
        I(1, "漢字欄", "G(4)", value="G'漢字欄名'"),
        I(1, "WS-END", "S9(4)", "COMP"),
        C("SHAINREC"),
    ],
    "units": [
        section("主処理"),
        para("開始", perform("集計"), raw("MOVE 見出し TO 社員番号"), goback()),
        para("集計", raw("ADD 1 TO 処理件数")),
    ],
}

KYUYO02 = {
    "member": "KYUYO02",
    "program_id": "KYUYO02",
    "member_horror": H46,
    "encoding": ("shift_jis", "lf"),
    "remarks": ["KYUYO02 - 賞与計算 (SHIFT-JIS, PC DOWNLOAD)"],
    "ws": [I(1, "賞与額", "9(7)", value="0"), I(1, "表題", "X(16)", value="'賞与明細'"),
           I(1, "WS-END", "S9(4)", "COMP")],
    "units": [para("賞与処理", raw("ADD 1000 TO 賞与額", "DISPLAY 表題"), goback())],
}

KYUYJP = {
    "member": "KYUYJP",
    "program_id": "給与計算",
    "program_id_horror": H40,
    "member_horror": H40,
    "remarks": ["KYUYJP - 給与計算 (REHOSTED, UTF-8)"],
    "encoding": ("utf-8", "lf"),
    "compile": "other-dialect",
    "compile_reason": "opensourcecobol4j dialect: GnuCOBOL 3.1 does not take the full-width space U+3000 as a separator",
    "compile_check": ("u3000-to-space", "every U+3000 is replaced by a space for the check; the rest compiles as written"),
    "phantoms": [{"channel": "data_moves", "target": "X", "horror": H40,
                  "why": "X項目 is one name: a move into it is not a move into X"}],
    "data_header": "DATA　DIVISION",
    "data_header_horror": H38,
    "ws": [
        I(1, "Ｆ０２", "X", sep="　", horror=H38),
        I(1, "社員コード", "X(6)"),
        I(1, "X項目", "X(4)"),
        I(1, "FIXED_FLD", "X(2)"),
        I(1, "ＴＥＳＴ−ＤＡＴＡ１", "X(2)", horror=H41),
        I(1, "ＴＥＳＴ−ＲＥＣＯＲＤ１", "X(2)", horror=H41),
        I(1, "ＴＥＳＴ－ＤＡＴＡ２", "X(2)", horror=H41),
        I(1, "WS-KYUY", copy=[CP("KYUYCPY", sep="　")], horror=H38),
    ],
    "units": [
        section("主処理"),
        para("開始",
             raw("MOVE '000001' TO 社員コード", "MOVE SPACES TO ＴＥＳＴ−ＤＡＴＡ１",
                 "MOVE 'AB' TO ＴＥＳＴ−ＲＥＣＯＲＤ１"),
             perform("Ｓ−初期化", horror=H41),
             goback()),
        section("Ｓ−初期化", horror=H41),
        para("初期化１", raw("MOVE SPACE TO X項目", "MOVE 'Z' TO Ｆ０２"), horror=H41),
    ],
}

APP = {
    "id": "KYUY",
    "title": "Japanese payroll (cp930, cp939, Shift-JIS, UTF-8)",
    "style": "DBCS: SO/SI in EBCDIC, Shift-JIS and UTF-8 members; Japanese and full-width names",
    "encodings": {"cobol": ("cp930", "fb80")},
    "copybooks": COPYBOOKS,
    "programs": [KYUYO01, KYUYO02, KYUYJP],
}
