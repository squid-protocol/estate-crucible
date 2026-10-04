# estate-crucible key format (`estate-crucible-key/1`)

This file defines what the answer key says and how to read it. The generator
(`python3 -m generator`) writes the key; `tools/check.py` enforces it.

## 1. Files

```
key/manifest.json          format, generator settings, apps, channels, fact totals, every member
key/apps/<APPID>.json      the facts of one app's members
key/apps/_shared.json      the facts of shared/ (copylib, proclib)
horrors/H-NNNN.json        one horror: its definition, where it is planted, its facts and phantoms
horrors/README.md          the horror index (generated)
spec/horrors.json          hand-written horror definitions (the only hand-edited input besides generator/)
```

Every path inside the key is relative to `estate/`, the directory a scanner is pointed
at. Line numbers are 1-based physical lines of the member.

### 1.1 `key/manifest.json`

| field | content |
|---|---|
| `format` | `estate-crucible-key/1` |
| `generator` | `version`, `seed`, `size`: the settings that reproduce the committed tree |
| `estate_root` | `estate` |
| `apps` | `id`, `title`, `style` per app |
| `channels` | the channel names, in order (section 3) |
| `fact_totals` | facts per channel, and `phantoms` |
| `horrors` | the horror ids |
| `members` | per member path: `app` (null for shared/), `library`, `language`, `sha256` of the member's bytes, `key` (the file holding its facts), `compile` (section 5), `generated_from`, `horrors` |

### 1.2 `key/apps/<APPID>.json`

`{"format", "app", "members": {path: entry}}`. An entry has `app`, `library`, `language`,
`numbered` (cols 1-6 carry sequence numbers), `lines`, `compile`, optional
`generated_from`, then one list per channel that has facts, then `phantoms` and `horrors`.

### 1.3 Code pages and storage

**Decision: members are committed as the exact bytes an export holds, never as a transcoded
view.** A PDS member transferred in binary is raw EBCDIC with no line ends; one kept in z/OS
UNIX is EBCDIC with NEL (X'15') line ends; one transferred as text, or written on a PC, is in
the PC's code page with LF. A scanner meets those bytes in a real estate, so the crucible
gives it the same. The key states, per member (`key/manifest.json` `members`):

| field | values |
|---|---|
| `encoding` | `utf-8`, `utf-8-sig` (with a byte-order mark), `shift_jis`, `cp037`, `cp273`, `cp277`, `cp420`, `cp930`, `cp939` |
| `storage` | `lf` (lines ending in LF), `nel` (raw EBCDIC, each line ending in X'15'), `fb80` (raw EBCDIC 80-byte records, blank-padded, no line ends) |
| `bytes`, `sha256` | of the committed file |

and `code_pages` maps every non-UTF-8 member's path to its code page: **what a scanner must
be told**. Nothing in a raw EBCDIC member's bytes names its page (cp037 and cp277 differ only
in a dozen national positions), so an estate's code pages are declared, and the scorer
passes this map to the scan (`--source-encoding PATH=CODEC,...`). Line numbers are records:
line n of an `fb80` member is its n-th 80-byte record.

* `.gitattributes` keeps git from converting any of it (`estate/** -text`) and marks every
  non-UTF-8 member `binary`; `tools/check.py` fails on a member it does not cover.
* `tools/view.py <member>` prints any member as text.
* The EBCDIC tables (`generator/codepages/*.json`) are built from GNU libc iconv by
  `tools/gen_codepages.py`, not from the JDK GitGalaxy's own tables come from, so the two
  implementations meet only in the scorer. cp930 / cp939 write every DBCS run between
  Shift-Out (X'0E') and Shift-In (X'0F'), balanced on each record. A horror that needs an
  unbalanced or nested shift writes it on purpose (in a comment line, where IBM allows any
  character).
* A fixed-format COBOL line never straddles column 72 in its own encoding's bytes, whichever
  way a reader counts columns.
* cp273 X'BC': glibc maps it to U+00AF, Python to U+203E. No member uses it.

## 2. Tags on facts

| key | meaning |
|---|---|
| `horror` | the fact was written inside horror H-NNNN's plant; the horror passes only when all its facts pass |
| `depends_on` | the fact is outside every plant but can only pass once these horrors are fixed (a CALL to a program whose PROGRAM-ID is a horror) |
| `alternatives` | (copies) other members an import may name instead of `resolves_to`: the BMS mapset a symbolic-map copybook is generated from |

## 3. Channels

| channel | one fact per | fields | asserts |
|---|---|---|---|
| `programs` | PROGRAM-ID paragraph; PL/I `OPTIONS(MAIN)` procedure | `program_id`, `line` | the program's name |
| `units` | paragraph, section, main line, PL/I procedure | `name` (null for the main line), `kind` (`paragraph` / `section` / `mainline` / `procedure`), `program` (when a member holds several programs), `section` (enclosing section), `start_line`, `end_line`, `span_end` (sections) | extent: from the header to the **last code line** before the next header (comments and blank lines after it are not part of the extent). A section's `end_line` is its own statements (its header when a paragraph follows at once); `span_end` is the section's full extent per IBM. The main line runs from the first statement after the PROCEDURE DIVISION header to the line before the first header |
| `edges` | PERFORM / GO TO / CALL statement | `kind` (`perform` / `goto` / `call`), `from` (unit name, null = main line), `target`, `line` (the verb's line), `thru`, `form` (calls: `literal` / `identifier`) | the procedure or program the statement names. A CALL identifier's `target` is the identifier |
| `call_sites` | CALL, EXEC CICS LINK / XCTL / RETURN TRANSID, JCL EXEC PGM | `verb`, `form`, `operand`, `target` (an identifier's VALUE), `line`, `resolves_to` (the member, or null outside the estate) | |
| `copies` | COPY, EXEC SQL INCLUDE | `member`, `kind` (`copy` / `sql-include`), `line`, `resolves_to` (null: supplied by CICS / Db2), `library` (COPY ... IN), `replacing` | resolution: `IN library` searches that library; otherwise SYSLIB order, the app's `<APP>CPY` (`copybook/`), `<APP>DCL` (`dclgen/`), then `SHRCPY` (`shared/copylib/`), first hit wins |
| `data_items` | data description entry (COBOL), DECLARE item (PL/I) | `level`, `name` (`FILLER` when omitted, with `implicit_filler`), `pic`, `usage` (the usage word, `USAGE` dropped; PL/I: the attributes), `occurs`, `redefines`, `value` (as written), `section`, `line`, `copy_members`, `sign_separate` / `sign_leading` | pseudo-text awaiting COPY REPLACING (`:TAG:-ID`) is not a data-name: a phantom, not a fact |
| `layouts` | 01 entry written in a program | `record`, `line`, `bytes`, `fields`: every elementary item in storage order with `name`, `level`, `pic`, `usage`, `offset`, `bytes`, `file`; `overlay: true` under a REDEFINES | COPY expanded. An item inside an OCCURS group is listed once at its first occurrence; `bytes` carries only its own OCCURS. Sizes: SPEC 6 |
| `sql_statements` | EXEC SQL statement | `verb`, `table`, `access`, `line` (EXEC SQL's line), `procedure` (CALL) | |
| `sql_tables` | EXEC SQL DECLARE TABLE | `table`, `line`, `columns` (`name`, `type`, `length`, `scale`, `nullable`, `line`) | |
| `jcl_steps` | EXEC statement | `job` or `proc`, `step`, `ordinal`, `program` or `exec_proc`, `cond`, `line` | |
| `jcl_dds` | DD statement | `job` or `proc`, `step`, `dd`, `dsn` (no generation), `generation`, `disp`, `disp_normal`, `sysout`, `line` | |
| `screen_fields` | DFHMSD / DFHMDI / DFHMDF | `kind`, `mapset`, `map`, `name`, `pos_line`, `pos_column`, `length`, `attrb`, `picin`, `initial`, `line` | |
| `csd_resources` | DEFINE | `type`, `name`, `group`, `line`, `program`, `dsname` | |
| `transactions` | DEFINE TRANSACTION | `transid`, `program`, `group`, `line`, `resolves_to` | |
| `cics_resources` | EXEC CICS command naming a resource | `verb`, `kind` (`MAP` / `FILE` / `QUEUE`), `name`, `qualifier` (mapset; TS / TD), `record` (INTO / FROM), `access` (read / write / update), `line` (EXEC CICS's line) | |
| `jcl_datasets` | DD naming a dataset | `dsn` (the base), `generation` (`0`, `+1`, `-1`), `step`, `dd`, `line` | the dataset a job or proc references; a reader may record a GDG reference as its base or with its generation, never anything else |
| `file_control` | FILE-CONTROL SELECT | `select`, `assign`, `organization`, `access_mode`, `record_key`, `file_status`, `fd_copies` (COPY members of its FD record), `line` | |
| `entry_points` | PROCEDURE DIVISION header (COBOL), external PROC (PL/I) | `kind` (`PROCEDURE`), `program`, `params` (USING / parameter list), `line` | |
| `data_moves` | source -> target pair of a data-moving statement (MOVE, ADD, SUBTRACT, COMPUTE, INITIALIZE, WRITE / REWRITE FROM, READ INTO; PL/I assignment) | `verb`, `source` (as written; null for INITIALIZE), `source_kind` (`item` / `literal` / `figurative` / `function` / `file`), `target` (with qualifiers, subscripts dropped), `corresponding`, `source_refmod` / `target_refmod` and their texts, `line` | the statement's line. The generator reads its own statement text with a small grammar (`generator/moves.py`); a moving verb in a form it does not know is an error, not a silent gap |
| `file_edges` | resolved invocation between two members | `kind` (`call` for CALL / LINK / XCTL, `exec` for EXEC PGM), `target` (member path) | one per (target, kind); a call inside the same member draws none |

## 4. Phantoms

`phantoms` lists facts that must **not** be recorded: `{"channel", ...the fact's
identifying fields..., "why", "horror"}`. A scorer reports every unkeyed fact as a
phantom anyway. An explicit phantom ties one to a horror and says why it is wrong, so
it can be attributed. Examples: an inline PERFORM's first header word as a callee, the
next line's sequence number as a split operand, IDMS-CONTROL as a unit.

## 5. Compile status (`compile`)

| status | meaning |
|---|---|
| `compiled` | `cobc -c -std=ibm` accepts the member as written |
| `compiled-stubbed` | accepted after EXEC SQL / EXEC CICS blocks become CONTINUE and EXEC SQL INCLUDE becomes COPY (the precompilers' job) |
| `ibm-only` | not compiled as written; `reason` says why. With `check_variant`, a variant with that one construct normalised is compiled, so the rest of the member is still checked |
| `other-dialect` | written for another compiler's dialect (opensourcecobol4j); `reason` says what GnuCOBOL refuses, and `check_variant` normalises that one construct |
| `copybook`, `not-cobol` | not compiled on its own |

A member with multi-byte characters is decoded to UTF-8 for the check and compiled as free
format (`cobc -free`, cols 1-6 and 73-80 dropped): in UTF-8 its lines are longer than in its
own code page.

## 6. Storage sizes

From Enterprise COBOL for z/OS, Language Reference, "USAGE clause", and Programming
Guide, "Examples: numeric data and internal representation":

* DISPLAY: one byte per character position; `S` and `V` take none, except that SIGN ... SEPARATE gives the sign a byte of its own.
* PIC N (USAGE NATIONAL, implied under NSYMBOL(NATIONAL)) and PIC G (USAGE DISPLAY-1): 2 bytes per character position. `data_items.usage` records these implied usages; an implied DISPLAY is recorded as no usage.
* BINARY / COMP / COMP-4 / COMP-5: 2, 4 or 8 bytes for 1-4, 5-9 or 10-18 digits.
* PACKED-DECIMAL / COMP-3: digits / 2 + 1 bytes (integer division).
* COMP-1: 4 bytes. COMP-2: 8 bytes.

## 7. Versioning

A change to what an existing field means bumps the major number (`estate-crucible-key/2`)
and the scorer that reads it. Adding a channel, an optional field or a tag does not.
