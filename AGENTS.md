# AGENTS.md — estate-crucible

Vendor-neutral guidance for any coding agent working in this repo. Repo-specific rules live
here. The multi-repo picture lives in the gitgalaxy engine repo's **`docs/ecosystem.md`**
(the constellation map, cross-repo workflow ordering, PR conventions). Read it before any
cross-repo work.

## What this repo is

The **estate crucible**: a synthetic z/OS estate (`estate/`) and its answer key (`key/`),
both written by the generator (`generator/`). Horrors (adversarial but valid constructs) are
planted in realistic applications; each carries the documentation citation for what its
key asserts (`spec/horrors.json`). The format is [`SPEC.md`](SPEC.md). gitgalaxy's
`tests/tools/estate_crucible.py` scores the engine against it (epic
[gitgalaxy#4317](https://github.com/squid-protocol/gitgalaxy/issues/4317)).

## Hard rules

1. **Never edit `estate/`, `key/` or `horrors/` by hand.** Change `generator/` or
   `spec/horrors.json`, run `python3 -m generator`, commit the regenerated tree with the
   change. `tools/check.py` fails on any hand edit.
2. **The key is truth, not tool output.** Never change the generator so that the key agrees
   with an engine. Change what the key asserts only when documentation shows the key was
   wrong; say so, with the citation, in the commit and in the horror's `notes`.
3. **When the engine and the key disagree, check the key as hard as the engine.** The
   generator can share the engine's blind spots. Read the member, find the IBM rule, then
   decide which side is wrong.
4. **Every horror cites its rule.** A `spec/horrors.json` entry needs `asserts` and at
   least one citation with `url`, `section` and the quoted rule. IBM documentation for
   COBOL, CICS, Db2, JCL; the vendor's own documentation for a non-IBM product (Broadcom
   for IDMS).
5. **Every planted program compiles** with `cobc -std=ibm` (as written, or with EXEC blocks
   stubbed), or is `ibm-only` with a `compile_reason`. Prefer a `compile_check` variant so
   the rest of an IBM-only member is still compiled.
6. **Plant horrors in realistic code.** A horror lives inside an application with the
   surrounding paragraphs, copybooks and JCL a real member would have. Keep one horror's
   facts from depending on another's where you can, so a failure points at one cause; use
   `depends_on` where you cannot.
7. **Original code only.** Nothing is copied from IBM samples, CardDemo, GenApp, CBSA or any
   other estate, not even a layout. Reproducers from gitgalaxy issues are shapes to plant,
   not text to paste.
8. **Generator: standard library only, deterministic.** All randomness goes through a
   seeded `random.Random`. Same seed and size, same bytes.
9. **Bytes are the estate.** A member's code page and record format are part of its spec
   (`encoding` on the app or the member). Never re-save a member through an editor or let
   git convert it; add a new non-UTF-8 member's path to `.gitattributes` as `binary`. New
   DBCS characters need `python3 tools/gen_codepages.py` (glibc iconv) before generating.
10. **Check before you push:** `make check` (or `make check-fast` without a compiler).
11. **Cross-repo PRs carry a "Cross-repo" note** (companion PR links, merge order, what
    re-runs after), per gitgalaxy's `docs/ecosystem.md`.

## Adding a horror

1. Add its definition to `spec/horrors.json`: next id, title, category, gitgalaxy issue,
   shapes, `asserts`, citations.
2. Plant it in an app under `generator/apps/` with `horror="H-NNNN"` on the statements,
   items or paragraphs it covers. If the shape needs a new rendering (a new statement form),
   add it to `generator/stmt.py` / `generator/cobol.py` so it records its own facts and
   phantoms.
3. `python3 -m generator`, then read the generated member and its `horrors/H-NNNN.json`:
   are the facts what IBM says? `make check`.
4. Run gitgalaxy's scorer against the branch (`ESTATE_CRUCIBLE_ALLOW_UNPINNED=1 python
   tests/tools/estate_crucible.py --crucible <this checkout>`). A new horror should fail
   while its gitgalaxy issue is open. If it passes, find out why before merging: a fixed
   bug, or a plant that misses.

## Adding an app

Add a module under `generator/apps/` that defines `APP` (see `acct.py`) and list it in
`generator/apps/__init__.py`. Member names follow PDS rules (1-8 characters, uppercase).

## Releases and the gitgalaxy pin

gitgalaxy pins this repo to a **release tag** in `tests/_estate_crucible_pin.py`
(`PINNED_REF`). Tagging is a deliberate, coordinated step: see [`RELEASING.md`](RELEASING.md).
Never create tags or releases as a side effect of other work.
