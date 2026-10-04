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

## 2. Tags on facts

| key | meaning |
|---|---|
| `horror` | the fact was written inside horror H-NNNN's plant; the horror passes only when all its facts pass |
| `depends_on` | the fact is outside every plant but can only pass once these horrors are fixed (a CALL to a program whose PROGRAM-ID is a horror) |
| `alternatives` | (copies) other members an import may name instead of `resolves_to`: the BMS mapset a symbolic-map copybook is generated from |

## 3. Channels

| channel | one fact per | fields | asserts |
|---|---|---|---|
| `programs` | PROGRAM-ID paragraph | `program_id`, `line` | the program's name |
| `units` | paragraph, section, main line | `name` (null for the main line), `kind` (`paragraph` / `section` / `mainline`), `section` (enclosing section), `start_line`, `end_line`, `span_end` (sections) | extent: from the header to the **last code line** before the next header (comments and blank lines after it are not part of the extent). A section's `end_line` is its own statements (its header when a paragraph follows at once); `span_end` is the section's full extent per IBM. The main line runs from the first statement after the PROCEDURE DIVISION header to the line before the first header |
| `edges` | PERFORM / GO TO / CALL statement | `kind` (`perform` / `goto` / `call`), `from` (unit name, null = main line), `target`, `line` (the verb's line), `thru`, `form` (calls: `literal` / `identifier`) | the procedure or program the statement names. A CALL identifier's `target` is the identifier |
| `call_sites` | CALL, EXEC CICS LINK / XCTL / RETURN TRANSID, JCL EXEC PGM | `verb`, `form`, `operand`, `target` (an identifier's VALUE), `line`, `resolves_to` (the member, or null outside the estate) | |
| `copies` | COPY, EXEC SQL INCLUDE | `member`, `kind` (`copy` / `sql-include`), `line`, `resolves_to` (null: supplied by CICS / Db2) | resolution follows SYSLIB order: the app's `copybook/`, its `dclgen/`, then `shared/copylib/` |
| `data_items` | data description entry | `level`, `name`, `pic`, `usage` (the usage word, `USAGE` dropped), `occurs`, `redefines`, `value` (as written), `section`, `line`, `copy_members` | |
| `layouts` | 01 entry written in a program | `record`, `line`, `bytes`, `fields`: every elementary item in storage order with `name`, `level`, `pic`, `usage`, `offset`, `bytes`, `file`; `overlay: true` under a REDEFINES | COPY expanded. An item inside an OCCURS group is listed once at its first occurrence; `bytes` carries only its own OCCURS. Sizes: SPEC 6 |
| `sql_statements` | EXEC SQL statement | `verb`, `table`, `access`, `line` (EXEC SQL's line), `procedure` (CALL) | |
| `sql_tables` | EXEC SQL DECLARE TABLE | `table`, `line`, `columns` (`name`, `type`, `length`, `scale`, `nullable`, `line`) | |
| `jcl_steps` | EXEC statement | `job` or `proc`, `step`, `ordinal`, `program` or `exec_proc`, `cond`, `line` | |
| `jcl_dds` | DD statement | `job` or `proc`, `step`, `dd`, `dsn` (no generation), `generation`, `disp`, `disp_normal`, `sysout`, `line` | |
| `screen_fields` | DFHMSD / DFHMDI / DFHMDF | `kind`, `mapset`, `map`, `name`, `pos_line`, `pos_column`, `length`, `attrb`, `picin`, `initial`, `line` | |
| `csd_resources` | DEFINE | `type`, `name`, `group`, `line`, `program`, `dsname` | |
| `transactions` | DEFINE TRANSACTION | `transid`, `program`, `group`, `line`, `resolves_to` | |

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
| `copybook`, `not-cobol` | not compiled on its own |

## 6. Storage sizes

From Enterprise COBOL for z/OS, Language Reference, "USAGE clause", and Programming
Guide, "Examples: numeric data and internal representation":

* DISPLAY: one byte per character position; `S` and `V` take none (no SIGN SEPARATE in phase 0).
* BINARY / COMP / COMP-4 / COMP-5: 2, 4 or 8 bytes for 1-4, 5-9 or 10-18 digits.
* PACKED-DECIMAL / COMP-3: digits / 2 + 1 bytes (integer division).
* COMP-1: 4 bytes. COMP-2: 8 bytes.

## 7. Versioning

A change to what an existing field means bumps the major number (`estate-crucible-key/2`)
and the scorer that reads it. Adding a channel, an optional field or a tag does not.
