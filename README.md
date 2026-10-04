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
  apps/<APPID>/jcl/              jobs                MEMBER.jcl
  apps/<APPID>/proclib/          cataloged procs     MEMBER.prc
  apps/<APPID>/bms/              BMS mapsets         MEMBER.bms
  apps/<APPID>/csd/              CSD definitions     GROUP.csd
  shared/copylib/  shared/proclib/   estate-wide libraries, searched after the app's own
key/                             the answer key (SPEC.md); generated
horrors/                         one record per horror, with its planted facts; generated
spec/horrors.json                horror definitions and citations; hand-written
generator/                       the generator (Python 3.9+, standard library only)
  apps/                          the applications, as data; filler.py makes seeded ones
tools/check.py                   regenerate + diff, key consistency, compile
tools/compile.py                 GnuCOBOL compile check; tools/stubs/ hold SQLCA / DFHAID / DFHEIBLK stand-ins
```

## The estate (phase 0)

| app | what it is | style |
|---|---|---|
| `ACCT` | nightly account posting: 4 programs, 6 copybooks, a job and a proc | ISPF sequence numbers in cols 1-6, change tags in 73-80, `PERFORM ... THRU` exit paragraphs, main-line code |
| `CUST` | customer inquiry: 3 CICS programs, a BMS mapset and its symbolic map, a CSD group, a DCLGEN, Db2 stored procedures | unnumbered, pseudo-conversational |
| `LOAN` | loan servicing: an IDMS-DC program, two batch programs, a job | mixed numbering; PROGRAM-ID periods missing |
| `shared` | `DATEWS` copybook, `AUDLOG` proc | |

27 members. The key holds 329 facts and 21 phantoms over 14 channels
(`key/manifest.json`, `fact_totals`).

## Horrors

| id | gitgalaxy issue | planted in | shape |
|---|---|---|---|
| H-0001 | [#4300](https://github.com/squid-protocol/gitgalaxy/issues/4300) | ACCTUPD | PERFORM / GO TO / CALL literal / CALL identifier / COPY with the operand on the next line, in a numbered member |
| H-0002 | [#4301](https://github.com/squid-protocol/gitgalaxy/issues/4301) | CUSTINQ, ACCTRPT | a conditional `EXEC CICS RETURN TRANSID` on its own line, a paragraph named `RETURN-TO-MENU`, `EXIT PERFORM` mid-paragraph |
| H-0003 | [#4302](https://github.com/squid-protocol/gitgalaxy/issues/4302) | ACCTPOST | main-line OPEN / PERFORM THRU / PERFORM UNTIL / GOBACK before the first paragraph |
| H-0004 | [#4303](https://github.com/squid-protocol/gitgalaxy/issues/4303) | ACCTRPT | `01 WS-RPT-HEAD.  COPY RPTHDR.` and two COPYs on one line |
| H-0005 | [#4304](https://github.com/squid-protocol/gitgalaxy/issues/4304) | CUSTDBIO | `EXEC SQL CALL PRODPROC.CUSTBAL (...)` and `EXEC SQL CALL CUSTAUDT` |
| H-0006 | [#4305](https://github.com/squid-protocol/gitgalaxy/issues/4305) | ACCTRPT, CUSTINQ | `PERFORM TEST AFTER/BEFORE`, `PERFORM WS-N TIMES`, `PERFORM 3 TIMES`, `EXIT PERFORM` |
| H-0007 | [#4306](https://github.com/squid-protocol/gitgalaxy/issues/4306) | LNIDMS01 | `IDMS-CONTROL SECTION. PROTOCOL. MODE IS IDMS-DC`, and the `SCHEMA SECTION` |
| H-0008 | [#4307](https://github.com/squid-protocol/gitgalaxy/issues/4307) | LNRATE, LNCALC | `PROGRAM-ID.    LNRATE` padded to col 72 with no period; `PROGRAM-ID LNCALC.` |

Each `horrors/H-NNNN.json` carries the definition, the citations, every planted member
and the exact facts and phantoms the key holds for it. `horrors/README.md` indexes them.

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

## Running the checks

```bash
make check          # regenerate + diff, key consistency, GnuCOBOL compile (cobc on PATH, else Docker)
make check-fast     # the same without compiling
make generate       # after changing generator/ or spec/: rewrite estate/, key/, horrors/
make scale-smoke    # the medium preset (12 seeded filler apps), twice, byte-identical
GNUCOBOL_IMAGE=gitgalaxy-gnucobol:3 python3 tools/compile.py
```

Compile results at phase 0: 9 programs compiled (4 as written, 3 with EXEC blocks stubbed,
2 IBM-only members through their check variant). One program, `LNIDMS01`, is not compiled:
it needs the CA IDMS DML precompiler.

## Scale

`python3 -m generator --size medium|large` (or `--filler-apps N`) adds seeded filler apps:
plain batch apps, fully keyed, no horrors, byte-identical for a given seed. Phase 4 of the
epic grows this dial to 20k-100k members. The committed tree is `--size small --seed 1`.

## Lower-confidence expected behaviour

| horror | point | basis |
|---|---|---|
| H-0008 | Enterprise COBOL compiles a PROGRAM-ID without its separator period (with a diagnostic). | #4307's evidence (CBLDB22 compiles in its course's own JCL). IBM's syntax diagram shows the period as required. The fact the key asserts (the program-name) does not depend on this. |
| H-0002 | `end_line` is the last code line, not the line before the next header. | IBM: a paragraph "ends immediately before the next paragraph-name or section header". Trailing comment lines carry no code, so the key stops at the last code line. A scorer comparing spans must treat trailing comments as equivalent. |

## Known gaps (phase 1 and later)

* Channels not keyed yet: CICS resource commands (`cics_resource_data`), data moves,
  file control (`file_control_data`), entry points, JCL dataset references, edge kinds
  `call` / `exec` in `edge_data`.
* The key states but no gitgalaxy column holds: PERFORM THRU's end, an EXEC SQL CALL's
  procedure name, SYSOUT DDs, REDEFINES overlays in a layout. The scorer reports these as
  `unscored`.
* Not planted yet: PL/I, Assembler, REXX; `PERFORM UNTIL EXIT`; nested and batch-compiled
  programs; COPY REPLACING; same-named members across libraries (SYSLIB order).

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
