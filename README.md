# estate-crucible

A synthetic z/OS application estate whose answer key is written by the same generator
that writes the code. Each application has COBOL, copybooks, JCL, PROCLIB, BMS, CSD and
DCLGEN members, laid out the way an exported estate is. Into it the generator plants
**horrors**: constructs that are valid (they compile) but hostile to a parser. For every
line it writes, the generator also records the facts a correct reader must extract, and
the facts it must **not** extract.

It is the oracle for [GitGalaxy](https://github.com/squid-protocol/gitgalaxy)'s mainframe
fact channels (epic [squid-protocol/gitgalaxy#4317](https://github.com/squid-protocol/gitgalaxy/issues/4317)).
gitgalaxy's `tests/tools/estate_crucible.py` scans `estate/`, reads the master DB, and
diffs every channel against the key: unit extents, PERFORM / GO TO / CALL edges, call
sites, COPY imports, data items, record layouts (offsets and lengths), SQL, JCL steps and
DDs, BMS fields, CSD resources. Counting is not enough. GitGalaxy#4301 (paragraphs cut at a
conditional GOBACK) and #4302 (main-line code in no unit) hid in keyed corpora because
those keys score unit names, not extents or edges.

## Ground rules

These come from the epic.

* **Every planted program compiles** under GnuCOBOL (`cobc -std=ibm`), or is labelled
  IBM-only with the reason. `tools/compile.py` checks it, and the status is part of the
  key (SPEC 5).
* **Every horror cites the documentation** for the behaviour its key asserts: the IBM
  page (or Broadcom's, for IDMS), the section, and the quoted rule (`spec/horrors.json`).
* **A generated key can share the generator's blind spots.** The generator records what
  it believes it wrote. It never reads the text back, so it cannot mis-parse it, but it
  can be wrong about COBOL. When the engine disagrees with the key, the key is checked as
  hard as the engine. A disagreement is a finding about one of the two until a citation
  settles it.
* **This complements real estates. It does not replace them.** Synthetic code cannot
  contain the horror nobody imagined. Real fresh estates
  ([gitgalaxy#3806](https://github.com/squid-protocol/gitgalaxy/issues/3806)) find
  horrors. This repo keeps each one found.
* **The key is generated, never edited.** `tools/check.py` regenerates the tree and fails
  on any difference from the committed one.

## Layout

```
estate/                          what a scanner is pointed at
  apps/<APPID>/cobol/            programs            MEMBER.cbl  (PDS member names: 1-8, uppercase)
  apps/<APPID>/copybook/         copybooks           MEMBER.cpy
  apps/<APPID>/dclgen/           DCLGEN output       MEMBER.dcl
  apps/<APPID>/oldcopy/          a retired copy library (<APP>OLD), still in some SYSLIBs   MEMBER.cpy
  apps/<APPID>/jcl/              jobs                MEMBER.jcl
  apps/<APPID>/proclib/          cataloged procs     MEMBER.prc
  apps/<APPID>/bms/              BMS mapsets         MEMBER.bms
  apps/<APPID>/csd/              CSD definitions     GROUP.csd
  apps/<APPID>/pli/              PL/I programs       MEMBER.pli
  shared/copylib/  shared/proclib/   estate-wide libraries, searched after the app's own
key/                             the answer key (SPEC.md); generated
horrors/                         one record per horror, with its planted facts; generated
spec/horrors.json                horror definitions and citations; hand-written
generator/                       the generator (Python 3.9+, standard library only)
  apps/                          the applications, as data; filler.py makes seeded ones
tools/check.py                   regenerate + diff, key consistency, compile
tools/compile.py                 GnuCOBOL compile check; tools/stubs/ hold SQLCA / DFHAID / DFHEIBLK stand-ins
```

## The estate (phase 3)

| app | what it is | style |
|---|---|---|
| `ACCT` | nightly account posting: 4 programs, 6 copybooks, a job and a proc | ISPF sequence numbers in cols 1-6, change tags in 73-80, `PERFORM ... THRU` exit paragraphs, main-line code |
| `CUST` | customer inquiry: 3 CICS programs, a BMS mapset and its symbolic map, a CSD group, a DCLGEN, Db2 stored procedures | unnumbered, pseudo-conversational |
| `LOAN` | loan servicing: an IDMS-DC program, two batch programs, a job | mixed numbering; PROGRAM-ID periods missing |
| `BILL` | monthly billing: a numbered batch program, a record copybook, a GDG job | empty numbered lines, change markers in cols 1-6, SIGN SEPARATE, unnamed FILLERs |
| `INVN` | inventory: a CICS program over a VSAM file and a TS queue, a Db2 module, a 60-line data-only copybook | a job named after a program, commented-out code |
| `PAYR` | payroll: one member holding PAYMAIN, a nested PAYCALC and a sibling `'PAYRPT'` | every COPY form; its own DATEWS shadowing the shared one |
| `GLED` | general ledger: the oldest code | numbered, cols 73-80 identification, every paragraph-header form |
| `MODN` | a rate service rehosted off z/OS | free-format source (not Enterprise COBOL) |
| `CLMS` | claims: a PL/I main program with internal procedures, calling a COBOL routine | PL/I |
| `NORD` | a Danish interest run: COBOL as raw EBCDIC cp277 80-byte records, copybooks with NEL line ends, PL/I and JCL in UTF-8 | Æ Ø Å in member, PROGRAM-ID (literal), PL/I and JCL names; EBCDIC collation; stray NUL bytes |
| `DEUT` | a German interest calculation in EBCDIC cp273 (NEL program, FB80 copybook) | `DECIMAL-POINT IS COMMA`, VALUE 1,50 in a copybook |
| `KYUY` | Japanese payroll in four encodings: cp930 FB80, cp939 NEL, Shift-JIS, UTF-8 (+ a UTF-8 copybook with a BOM) | DBCS words and literals with SO/SI, unbalanced / nested shift codes in comments, full-width names and spaces |
| `GULF` | an Arabic account inquiry: BMS in EBCDIC cp420 with visual-order text, program in cp037 | BiDi |
| `ORDR` | order entry: the edit routine ORDVAL and its forks ORDVALV2, ORDVOLD and ORDV#OLD (a member copy still saying `PROGRAM-ID. ORDVAL.`); ORDREC in three libraries with three layouts | per-program SYSLIB (ORDVOLD reads the retired ORDROLD first); a dead paragraph whose PERFORM is commented out; an orphan copybook; a job step for a deleted program |
| `SHIP` | shipment inquiry (CICS), an incomplete export: XCTL / LINK / CSD PROGRAM / TRANSACTION of programs that were never exported; a linkage COPY named like its program | a dead pre-migration fork |
| `TAXR` | tax withholding: TAXCALC2 replaced TAXCALC, which was never deleted; its own ADDRREC shadows the shared one; a vendor CALL | numbered; a Y2K paragraph nothing performs; a retired library holding an orphan |
| `DECO` | a decommissioned app: no programs left, only its job, CSD group and record copybook | every reference a gap |
| `LEGL` | general-ledger reconciliation from 1983 | comment banners before IDENTIFICATION DIVISION, change logs quoting old CALL / COPY / PERFORM text, `/` page ejects, sequence numbers and the deck name in cols 73-80 of every line |
| `PCED` | a pricing tool edited on PCs | TABs and trailing white space; a member in lower case; a free-format member |
| `RPTS` | management reports | report headings as VALUE literals continued past column 72 |
| `shared` | `DATEWS`, `ORDREC` and `ADDRREC` copybooks (library `SHRCPY`), `AUDLOG` proc | |

98 members. The key holds 1,353 facts and 46 phantoms over 23 channels
(`key/manifest.json`, `fact_totals`). Copy libraries are named the way `COPY ... IN
library` names them: `<APP>CPY`, `<APP>DCL`, `SHRCPY` and a retired `<APP>OLD`; a program's
SYSLIB is, by default, its app's libraries, then `SHRCPY`, then `<APP>OLD`.
`key/manifest.json` `copy_libraries` declares every library and SYSLIB order, in the shape
gitgalaxy's `--copy-libraries` reads ([SPEC.md](SPEC.md#14-copy-libraries-copy_libraries)).

## Horrors

60 horrors, each in `horrors/H-NNNN.json`; `horrors/README.md` is the index.

| ids | from | what |
|---|---|---|
| H-0001..H-0008 | gitgalaxy [#4300](https://github.com/squid-protocol/gitgalaxy/issues/4300)-[#4307](https://github.com/squid-protocol/gitgalaxy/issues/4307) | the phase-0 seeds: split operands, cut paragraphs (now also PL/I `ELSE RETURN;`), main-line code, same-line COPY, EXEC SQL CALL, inline PERFORM forms, IDMS sections (now also `SCHEMA SECTION`), period-less PROGRAM-ID |
| H-0009..H-0012 | [#4329](https://github.com/squid-protocol/gitgalaxy/issues/4329)-[#4332](https://github.com/squid-protocol/gitgalaxy/issues/4332) | found by this crucible's v0.1.0 scorecard: USAGE read into the PROCEDURE DIVISION, a COPY holding its own 01 folded into the 01 above, GDG `(+1)` truncated, numbered blank lines extending units |
| H-0013..H-0032 | gitgalaxy's field-testing ledger (`tests/cobol_mainframe/field_testing.json`, D001-D044), each citing its issue | every plantable defect: cols 73-80, change markers, DCLGEN, COPY forms, one-line INCLUDE, data-only copybooks, PROGRAM-ID forms, paragraph-header forms, commented code, ENVIRONMENT paragraphs, CSD / job name clashes, SIGN SEPARATE, END-/mixed-case names, free format, implicit FILLER, multi-program members, ASSIGN continuation |
| H-0033 | Enterprise COBOL 6.4 | `PERFORM UNTIL EXIT` |
| H-0034 | [#4265](https://github.com/squid-protocol/gitgalaxy/issues/4265) | the same copybook name in two libraries |
| H-0050..H-0060 | phase 3, estate realism (`realism`: why real estates hold it), [#4265](https://github.com/squid-protocol/gitgalaxy/issues/4265), [#4391](https://github.com/squid-protocol/gitgalaxy/issues/4391) | a stale member copy with its original's PROGRAM-ID, dead forks, copybook drift across three libraries with per-program SYSLIB and the collisions a scan should report, COPY of a missing member named like a program, references to programs the estate lacks, dead paragraphs and orphan copybooks, card-era comment banners, TABs and trailing white space, lower-case source, a continued VALUE literal |
| H-0035..H-0049 | gitgalaxy [#3988](https://github.com/squid-protocol/gitgalaxy/issues/3988) and the ledger's national-language defects | raw EBCDIC (FB80 and NEL), stray NULs (D016), the full-width space (D030), Nordic names (D015), Japanese and full-width names (D029, D031), DBCS literals and shift codes, decimal comma (#3942), EBCDIC collation, BiDi BMS (cp420), Shift-JIS, and the data-move defects D013, D023, D039 |

The ledger defects that cannot be planted yet are listed, with the reason, at the end of
`horrors/README.md` (reachability, data moves, multicultural forms, PL/I CICS and layouts,
non-IBM dialects, documentation defects).

A fact outside every plant that can only pass once a horror is fixed carries
`depends_on` (a call to a program whose PROGRAM-ID is a horror, every program's last
DATA DIVISION entry, every COPY of a member that exists in two libraries). Scorers report
those as the horror's cascade.

## The answer key

The full format is [SPEC.md](SPEC.md) (`estate-crucible-key/1`). One edge from H-0001, as
the key writes it:

```json
{"kind": "perform", "from": "0000-MAIN", "target": "2000-APPLY-UPDATES", "line": 20, "horror": "H-0001"}
```

and the phantom beside it, the fact a reader must not record:

```json
{"channel": "edges", "kind": "perform", "from": "0000-MAIN", "target": "002100",
 "why": "the sequence number of the line after a split PERFORM, not 2000-APPLY-UPDATES", "horror": "H-0001"}
```

A unit records its extent, not only its name:

```json
{"name": "RETURN-TO-MENU", "kind": "paragraph", "section": null, "start_line": 48, "end_line": 53, "horror": "H-0002"}
```

## Code pages

Members are committed as the bytes an export holds: raw EBCDIC (cp037, cp273, cp277, cp420,
cp930, cp939) as 80-byte records or with NEL line ends, Shift-JIS, UTF-8 with and without a
byte-order mark. `key/manifest.json` gives each member's `encoding` and `storage`, and
`code_pages` is what a scanner must be told. `python3 tools/view.py <member>` prints any of
them. The decision and the details are in [SPEC.md](SPEC.md#13-code-pages-and-storage).

## Running the checks

```bash
make check          # regenerate + diff, key consistency, GnuCOBOL compile (cobc on PATH, else Docker)
make check-fast     # the same without compiling
make generate       # after changing generator/ or spec/: rewrite estate/, key/, horrors/
make scale-smoke    # the medium preset (12 seeded filler apps), twice, byte-identical
GNUCOBOL_IMAGE=gitgalaxy-gnucobol:3 python3 tools/compile.py
```

Compile results at phase 3: 39 programs compile with `cobc -c -std=ibm`, each with its own
SYSLIB order. Three `incomplete` members COPY a member the estate lacks (a gap, H-0053); they
compile with a one-byte FILLER standing in for it. Members with
multi-byte characters are decoded to UTF-8 and compiled as free format. Some compile through
a check variant: two have the PROGRAM-ID period restored, KYUYO01 has PIC G turned into
PIC N (GnuCOBOL has no DBCS category), and KYUYJP has its full-width spaces turned into
spaces (opensourcecobol4j dialect). Four members are not compiled: `LNIDMS01` (IDMS) and the
PL/I members `CLMPROC`, `RENTEØ` and `NULREST`.

## Scale

`python3 -m generator --size medium|large` (or `--filler-apps N`) adds seeded filler apps:
plain batch apps, fully keyed, no horrors, byte-identical for a given seed. Phase 4 of the
epic grows this dial to 20k-100k members. The committed tree is `--size small --seed 1`.

## Lower-confidence expected behaviour

| horror | point | basis |
|---|---|---|
| H-0008 | Enterprise COBOL compiles a PROGRAM-ID without its separator period (with a diagnostic). | #4307's evidence (CBLDB22 compiles in its course's own JCL). IBM's syntax diagram shows the period as required. The fact the key asserts (the program-name) does not depend on this. |
| H-0002, every unit | `end_line` is the last code line, not the line before the next header. | IBM: a paragraph "ends immediately before the next paragraph-name or section header". Trailing comment and blank lines carry no code, so the key stops at the last code line. |
| H-0020 | A paragraph-name's separator period may stand alone on the next line. | No IBM sentence says so outright; it follows from the separator and continuation rules (an end of line is a space; a space may precede a separator period). GnuCOBOL `-std=ibm` accepts it. |
| H-0028 | Free-format source. | Not Enterprise COBOL for z/OS (72-column reference format only); cited from GnuCOBOL. It stands for code rehosted off the mainframe. |
| H-0033 | `PERFORM UNTIL EXIT`. | New in Enterprise COBOL 6.4: an estate compiled with 6.3 or earlier cannot hold it. |
| H-0037 | A compiler takes stray NULs inside a comment. | The ledger's evidence (DSF's PL/I programs compile with them); IBM says where a comment may stand, not which bytes it may hold. |
| H-0038, H-0040, H-0041 | The full-width space as a separator; mixed SBCS/DBCS names (X項目); a Japanese PROGRAM-ID; U+2212 as a hyphen. | Not Enterprise COBOL (DBCS words must be all double-byte, and words are separated by single-byte spaces): the opensourcecobol4j dialect, evidenced by its test suite (#3956, #3991). |
| H-0042 | Unbalanced and nested shift codes. | Planted only in comment lines: IBM forbids them in literals and words. |
| H-0045 | CCSID 420 host text is held in visual order. | IBM's emulator documentation (Lam-Alef stored as one character in visual CCSID 420), not the CICS BMS reference. |
| H-0050 | `CALL 'ORDVAL'` reaches the member ORDVAL, not ORDV#OLD (which also says `PROGRAM-ID. ORDVAL.`). | IBM requires the PROGRAM-ID to equal the program object's name; that the object is linked under its source member's name is the standard compile-and-link convention, not a language rule. |
| H-0058 | TABs between words are white space. | Enterprise COBOL documents no TAB in source; GnuCOBOL expands it to a tab stop (`-ftab-width`). |
| H-0013, H-0032 | Cols 73-80 are ignored. | The 6.4 Language Reference defines a 72-character line and does not describe cols 73-80 for source. |

## Known gaps (phase 3 and later)

* Channels not keyed yet: liveness (the `dead` channel keys only what nothing reaches),
  MOVE truncation (D038), COMMAREA contracts, DL/I and MQ calls, PL/I structure mapping and
  PL/I CICS operations.
* The key states but no gitgalaxy column holds: PERFORM THRU's end, an EXEC SQL CALL's
  procedure name, SYSOUT DDs, REDEFINES overlays in a layout. The scorer reports these as
  `unscored`.
* Not planted yet (estate realism, next): compile JCL whose SYSLIB DD concatenation is the
  evidence for a SYSLIB order, JCL symbolic parameters and INCLUDE groups, Assembler and
  REXX members, a nested COPY inside a drifting copybook, a CICS fork that is still in the
  CSD, PROCs overridden per step, more apps toward the epic's 30.

## Licence

Apache-2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). Every member is written by the
generator in this repository; nothing is copied from IBM samples, CardDemo, GenApp, CBSA or
any other estate. The `tools/stubs/` copybooks are stand-ins written from the documented
field names, used only for the compile check.

## The GitGalaxy constellation

This repo is one strand of the web of repos around
[GitGalaxy](https://github.com/squid-protocol/gitgalaxy). See gitgalaxy's
`docs/ecosystem.md` for the map. Its siblings:
[language-crucible](https://github.com/squid-protocol/language-crucible) (real hostile code,
no complete key) and [cics-crucible](https://github.com/squid-protocol/cics-crucible)
(hand-written CICS semantics for the translator). This one is a synthetic estate with a
complete, generated key, for the parser's facts.
