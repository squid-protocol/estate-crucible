"""Seeded filler apps: the scale dial (phase 4 grows this). Plain, horror-free batch apps
whose facts are as fully keyed as the hand-written ones. Everything comes from `rng`, so
a seed and a count always give the same members, byte for byte."""

from __future__ import annotations

import random
from typing import Any

from ..data import I
from ..stmt import call, goback, if_, para, perform, raw

_PICS = [("X(8)", None), ("X(20)", None), ("9(5)", None), ("S9(7)V99", "COMP-3"), ("S9(4)", "COMP"),
         ("S9(9)", "COMP"), ("9(8)", None), ("X", None)]
_VERBS = ["EDIT", "LOAD", "CALC", "POST", "SORT", "MERGE", "CHECK", "WRITE", "FORMAT", "TOTAL", "PURGE", "STAGE"]
_NOUNS = ["INPUT", "RECORD", "TOTALS", "HEADER", "DETAIL", "LIMITS", "RATES", "BATCH", "AUDIT", "KEYS"]


def make_app(rng: random.Random, n: int) -> dict[str, Any]:
    app_id = f"F{n:03d}"
    prefix = f"F{n:03d}"
    numbered = rng.random() < 0.6
    rec = f"{prefix}REC"
    fields = []
    for i in range(rng.randint(4, 9)):
        pic, usage = rng.choice(_PICS)
        fields.append(I(5, f"{prefix}-FLD-{i + 1:02d}", pic, usage))
    copybooks = [{"member": rec, "numbered": numbered, "header": [f" {rec} - {app_id} WORK RECORD"],
                  "items": fields}]
    n_progs = rng.randint(2, 5)
    names = [f"{prefix}P{i + 1:02d}" for i in range(n_progs)]
    programs = []
    for pi, name in enumerate(names):
        n_paras = rng.randint(4, 10)
        pnames = ["0000-MAIN"] + [
            f"{(i + 1) * 1000:04d}-{rng.choice(_VERBS)}-{rng.choice(_NOUNS)}" for i in range(n_paras - 1)
        ]
        units = []
        for i, pn in enumerate(pnames):
            stmts = [raw(f"ADD 1 TO WS-{prefix}-COUNT")]
            later = pnames[i + 1:]
            for tgt in rng.sample(later, k=min(len(later), rng.randint(0, 2))) if i else later[: rng.randint(1, 3)]:
                stmts.append(perform(tgt) if rng.random() < 0.7 else
                             if_(f"WS-{prefix}-COUNT > {rng.randint(1, 99)}", [perform(tgt)]))
            if i == 0 and pi + 1 < n_progs and rng.random() < 0.6:
                stmts.append(call(names[pi + 1], using=[f"WS-{prefix}-AREA"]))
            if i == 0:
                stmts.append(goback())
            units.append(para(pn, *stmts))
        programs.append({
            "member": name, "program_id": name, "numbered": numbered, "author": f"{app_id} TEAM",
            "remarks": [f"{name} - GENERATED FILLER PROGRAM ({app_id})"],
            "ws": [I(1, f"WS-{prefix}-AREA", copy=[rec]), I(1, f"WS-{prefix}-COUNT", "S9(7)", "COMP-3", value="ZERO")],
            "units": units,
        })
    jobs = [{"name": f"{prefix}JOB", "title": f"{app_id} DAILY", "steps": [
        {"name": f"STEP{(i + 1) * 10:03d}", "pgm": name, "dds": [
            {"name": "STEPLIB", "dsn": f"PROD.{app_id}.LOADLIB", "disp": ("SHR",)},
            {"name": "SYSOUT", "sysout": "*"},
        ]} for i, name in enumerate(names)]}]
    return {"id": app_id, "title": f"Filler app {app_id}", "style": "seeded filler", "copybooks": copybooks,
            "programs": programs, "jcl": jobs}


def filler_apps(seed: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    return [make_app(rng, i + 1) for i in range(count)]
