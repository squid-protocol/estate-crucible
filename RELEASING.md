# Releasing / tagging this repo

A tag here is what gitgalaxy measures against. This file exists so that cutting one is a
deliberate, coordinated decision, never an accident and never a silent change to what
gitgalaxy's scorer reports.

## How the pin works

This mirrors [cics-crucible's `RELEASING.md`](https://github.com/squid-protocol/cics-crucible/blob/main/RELEASING.md).
gitgalaxy reads this repo **at a release tag**, never at `main`, through one pin:
`[estate] ref` in gitgalaxy's `tests/crucible_pins.toml`. The scorer
(`tests/tools/estate_crucible.py`) refuses an off-pin checkout unless
`ESTATE_CRUCIBLE_ALLOW_UNPINNED=1`. There is no GitHub Actions variable: when the scorer
becomes a CI gate (phase 5 of gitgalaxy#4317), the workflow reads the pin from that file.

## The checklist, in order

1. **Batch, don't tag per PR.** A tag is a checkpoint. Let several PRs land on `main`
   first, each green on `make check`.
2. **In gitgalaxy**, with a local checkout of this repo's `main` at the commit you intend
   to tag, run the scorer (`ESTATE_CRUCIBLE_ALLOW_UNPINNED=1 python
   tests/tools/estate_crucible.py --crucible <checkout> --md scorecard.md`). Read every
   change against the previous tag's scorecard. A newly passing horror needs a reason (its
   bug was fixed). A newly failing check on unchanged code is a gitgalaxy regression; a
   newly failing check on new code is a finding for one of the two sides (AGENTS.md rule 3).
3. **Here**, cut the tag against exactly that commit, three-part semver:
   ```bash
   git tag -a vX.Y.Z -m "..." <commit>
   git push origin vX.Y.Z
   gh release create vX.Y.Z --notes-file <notes>
   ```
   Release notes list the horrors and apps added or changed, any key-format change (with
   the SPEC version), and any key correction with its citation.
4. **Back in gitgalaxy**, bump `ref` under `[estate]` in `tests/crucible_pins.toml`, grep for the old tag, and put the scorecard in
   the PR body.

Steps 2 and 4 happen in a different repository. Treat them as one coordinated cross-repo
change (with a "Cross-repo" PR note), not something to do unilaterally from this side.

## Where things stand

| Tag | Date | Contents |
|---|---|---|
| `v0.7.0` | 2026-11-04 | Open World batch (gitgalaxy#7065): Batch Badlands slices 4-6 (H-0083..H-0085 INCLUDE group, SET, NULLFILE, added DD; H-0094, H-0095 OUTPUT statements and RERUN; H-0102..H-0105 utilities), Hierarchy Keep app HKEP (H-0096..H-0098, IMS DBD SEGM order and GN/GB), Warlords of the Message Seas H-0100, H-0101, INVT H-0099, Alternate Index Archipelago H-0106..H-0108; 25 apps; channels `jcl_outputs`, `dli_calls`, `ims_gen`; new optional fields (SPEC section 3), format still `estate-crucible-key/1`. No key corrections. Scored against v0.6.0 with gitgalaxy 997dd1fb6: no unchanged horror changed except H-0071, which fails on the new JCLLIB phantoms (engine fix gitgalaxy#7693). |
| `v0.6.0` | 2026-11-02 | Open World level estates (gitgalaxy#7065): Batch Badlands (BDLD app, `jcl_utility_cards` channel, H-0064..H-0075), Alternate Index Archipelago (AIXA, H-0076..H-0082), Warlords of the Message Seas (MQSA, H-0086..H-0093). No key-format change, no key correction. |
| `v0.5.0` | 2026-10-28 | INVT era-1 batch app + JCL, era tags H-0001..H-0062, H-0061 BLL cells, H-0062 SERVICE RELOAD, H-0063 pre-RDO CICS resource macro tables in HLASM. |
| `v0.4.0` | 2026-10-05 | Phase 3 (estate realism): 7 apps (ORDR, SHIP, TAXR, DECO, LEGL, PCED, RPTS), 20 apps and 98 members; channels `copy_collisions`, `gaps`, `dead` (23 channels); `copy_libraries` in the manifest (retired `<APP>OLD` libraries, per-program SYSLIB orders); compile status `incomplete`; horrors H-0050..H-0060. Key correction: PL/I procedures end at their own `END name;` (SPEC 3.1; NULREST's `end_line` moves from its RETURN to its END). |
| `v0.3.0` | 2026-10-04 | Phase 2 (multicultural, gitgalaxy#3988): members committed as raw exported bytes (EBCDIC cp037/273/277/420/930/939 as FB80 or NEL, Shift-JIS, UTF-8 with and without BOM) with `encoding` / `storage` / `code_pages` in the key; 4 apps (NORD, DEUT, KYUY, GULF), 63 members; a `data_moves` channel (20 channels); horrors H-0035..H-0049. |
| `v0.2.0` | 2026-10-04 | Phase 1 of gitgalaxy#4317: 9 apps, 48 members, 19 channels (new: cics_resources, jcl_datasets, file_control, entry_points, file_edges), 34 horrors: H-0009..H-0012 (gitgalaxy#4329-#4332), H-0013..H-0032 from the field-testing ledger, PERFORM UNTIL EXIT, SYSLIB collisions (#4265); PL/I and free-format members; COPY ... IN library. |
| `v0.1.0` | 2026-10-04 | Phase 0 of gitgalaxy#4317: format `estate-crucible-key/1`, the generator, 3 apps (ACCT, CUST, LOAN) + shared libraries, 27 members, 14 channels, the 8 seed horrors H-0001..H-0008 from gitgalaxy#4300-#4307. First pinned by gitgalaxy's scorer PR. |
