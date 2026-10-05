"""Builds the whole estate: every member, the answer key and the horror catalog.

An app is data (see generator/apps/): its programs, copybooks, JCL, procs, BMS, CSD and
DCLGEN as specs. This module places each member where a z/OS export would put it,
resolves COPY / CALL / EXEC PGM across the estate, renders, and collects the facts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from . import FORMAT, VERSION
from .cobol import all_programs, write_copybook, write_program
from .data import Item
from .model import CHANNELS, Member
from .other import symbolic_map, write_bms, write_csd, write_dclgen, write_jcl
from .pli import write_pli

# library -> file extension, as GitGalaxy (and most exporters) recognise members
EXT = {"cobol": ".cbl", "copybook": ".cpy", "jcl": ".jcl", "proclib": ".prc", "bms": ".bms", "csd": ".csd",
       "dclgen": ".dcl", "copylib": ".cpy", "pli": ".pli", "oldcopy": ".cpy"}
LANG = {"cobol": "cobol", "copybook": "cobol", "copylib": "cobol", "dclgen": "cobol", "jcl": "jcl",
        "proclib": "jcl", "bms": "bms", "csd": "csd", "pli": "pli", "oldcopy": "cobol"}
SHARED_COPYLIB = "SHRCPY"
# an app's copy libraries: directory under apps/<APP>/ -> library-name suffix (<APP>CPY, ...)
APP_LIBRARIES = (("copybook", "CPY"), ("dclgen", "DCL"), ("oldcopy", "OLD"))

# Names a reference may leave unresolved without being a gap in the estate: members the
# runtime, the precompilers or the system supply (SPEC 3, `gaps`).
SYSTEM_MEMBERS = frozenset({
    "SQLCA", "SQLDA", "DFHAID", "DFHBMSCA", "DFHEIBLK", "DFHCOMMAREA",
    "IEBGENER", "IEFBR14", "IDCAMS", "SORT", "ICETOOL", "IKJEFT01", "IKJEFT1B", "DSNUTILB", "DFSRRC00", "DSNTIAR",
})


def syslib(app: Optional[str], has_old: bool = False) -> list[str]:
    """The copy libraries a program of `app` is compiled with, in SYSLIB order. A library's
    name is what `COPY member IN library` names: <APP>CPY, <APP>DCL, SHRCPY, and last an
    app's retired <APP>OLD library when it has one. An app or a program can declare its own
    order (`syslib`)."""
    return ([f"{app}CPY", f"{app}DCL"] if app else []) + [SHARED_COPYLIB] + ([f"{app}OLD"] if has_old else [])


def member_path(app: Optional[str], library: str, member: str) -> str:
    if len(member) > 8 or member != member.upper():
        raise ValueError(f"{member}: a PDS member name is 1-8 uppercase characters")
    base = f"apps/{app}" if app else "shared"
    return f"{base}/{library}/{member}{EXT[library]}"


class Estate:
    def __init__(self, apps: list[dict[str, Any]], shared: dict[str, Any], horrors: list[dict[str, Any]],
                 seed: int, size: str) -> None:
        self.apps = apps
        self.shared = shared
        self.horror_defs = {h["id"]: h for h in horrors}
        self.not_planted: list[dict[str, Any]] = []
        self._app_encodings: dict[Optional[str], dict[str, tuple[str, str]]] = {
            a["id"]: a.get("encodings", {}) for a in apps}
        self.seed = seed
        self.size = size
        self.members: dict[str, Member] = {}
        self.program_paths: dict[str, str] = {}
        # every member a PROGRAM-ID is written in (a stale copy keeps its original's PROGRAM-ID)
        self.program_members: dict[str, list[str]] = {}
        # app -> its SYSLIB order; program member path -> a program's own order
        self.app_syslib: dict[str, list[str]] = {}
        self.program_syslib: dict[str, list[str]] = {}
        # (library, member) -> (path, items)
        self.copybooks: dict[tuple[str, str], tuple[str, list[Item]]] = {}

    # ------------------------------------------------------------ registry
    def _register(self) -> None:
        for app in self.apps:
            a = app["id"]
            self.app_syslib[a] = app.get("syslib") or syslib(a, bool(app.get("old_copybooks")))
            for p in app.get("programs", []):
                path = member_path(a, "cobol", p["member"])
                if p.get("syslib"):
                    self.program_syslib[path] = p["syslib"]
                for prog in all_programs(p):
                    pid = prog["program_id"].upper()
                    self.program_members.setdefault(pid, []).append(path)
                    if p.get("stale_copy"):
                        # a member copied under a new name with its PROGRAM-ID left alone: a
                        # dynamic CALL loads the load module named for the program, never it
                        continue
                    if pid in self.program_paths:
                        raise ValueError(f"PROGRAM-ID {pid} defined twice")
                    self.program_paths[pid] = path
            for cb in app.get("copybooks", []):
                self.copybooks[(f"{a}CPY", cb["member"])] = (member_path(a, "copybook", cb["member"]), cb["items"])
            for cb in app.get("old_copybooks", []):
                self.copybooks[(f"{a}OLD", cb["member"])] = (member_path(a, "oldcopy", cb["member"]), cb["items"])
            for bms in app.get("bms", []):
                self.copybooks[(f"{a}CPY", bms["mapset"])] = (member_path(a, "copybook", bms["mapset"]),
                                                             symbolic_map(bms))
            for d in app.get("dclgen", []):
                self.copybooks[(f"{a}DCL", d["member"])] = (member_path(a, "dclgen", d["member"]), [])
        for cb in self.shared.get("copylib", []):
            self.copybooks[(SHARED_COPYLIB, cb["member"])] = (member_path(None, "copylib", cb["member"]), cb["items"])

    def order_of(self, app: Optional[str], path: Optional[str] = None) -> list[str]:
        """The SYSLIB order of the member at `path` (a program's own, else its app's)."""
        if path and path in self.program_syslib:
            return self.program_syslib[path]
        return self.app_syslib.get(app or "", syslib(app))

    def resolver(self, app: Optional[str], path: Optional[str] = None):
        """COPY resolution: `IN library` searches that library only; otherwise SYSLIB order
        (the program's or app's order, by default the app's copybook and DCLGEN libraries,
        then shared/copylib, then a retired OLD library), first hit wins."""
        order = self.order_of(app, path)

        def resolve(member: str, lib: Optional[str] = None) -> tuple[Optional[str], Optional[list[Item]]]:
            for library in [lib] if lib else order:
                hit = self.copybooks.get((library, member))
                if hit:
                    return hit
            return None, None

        return resolve

    def _new(self, app: Optional[str], library: str, member: str, numbered: bool = False,
             free: bool = False, spec: Optional[dict[str, Any]] = None) -> Member:
        path = member_path(app, library, member)
        if path in self.members:
            raise ValueError(f"{path} written twice")
        # code page and record format: the member's own, else its app's for that library, else UTF-8
        enc = (spec or {}).get("encoding") or self._app_encodings.get(app, {}).get(library) or ("utf-8", "lf")
        m = Member(path, LANG[library], app=app, library=library, numbered=numbered, free=free,
                   encoding=enc[0], storage=enc[1])
        self.members[path] = m
        return m

    # ------------------------------------------------------------ build
    def build(self) -> None:
        self._register()
        for app in self.apps:
            a = app["id"]
            resolve = self.resolver(a)
            for cb in app.get("copybooks", []):
                write_copybook(self._new(a, "copybook", cb["member"], cb.get("numbered", False), spec=cb), cb, resolve)
            for cb in app.get("old_copybooks", []):
                write_copybook(self._new(a, "oldcopy", cb["member"], cb.get("numbered", False), spec=cb), cb, resolve)
            for bms in app.get("bms", []):
                write_bms(self._new(a, "bms", bms["mapset"], spec=bms), bms)
                sym = {"header": [f" SYMBOLIC MAP FOR MAPSET {bms['mapset']} -- GENERATED BY BMS ASSEMBLY"],
                       "items": symbolic_map(bms)}
                sm = self._new(a, "copybook", bms["mapset"])
                write_copybook(sm, sym, resolve)
                sm.generated_from = member_path(a, "bms", bms["mapset"])
            for d in app.get("dclgen", []):
                write_dclgen(self._new(a, "dclgen", d["member"]), d)
            for p in app.get("programs", []):
                pm = self._new(a, "cobol", p["member"], p.get("numbered", False), p.get("free", False), spec=p)
                for opt in ("lower", "tabs", "ident"):
                    setattr(pm, opt, p.get(opt, getattr(pm, opt)))
                write_program(pm, p, self.resolver(a, pm.path), self.program_paths)
            for pl in app.get("pli", []):
                write_pli(self._new(a, "pli", pl["member"], spec=pl), pl, self.program_paths)
            for j in app.get("jcl", []):
                write_jcl(self._new(a, "jcl", j["name"], spec=j), j, self.program_paths, proc=False)
            for pr in app.get("procs", []):
                write_jcl(self._new(a, "proclib", pr["name"]), pr, self.program_paths, proc=True)
            for c in app.get("csd", []):
                write_csd(self._new(a, "csd", c["group"]), c, self.program_paths)
        resolve = self.resolver(None)
        for cb in self.shared.get("copylib", []):
            write_copybook(self._new(None, "copylib", cb["member"]), cb, resolve)
        for pr in self.shared.get("proclib", []):
            write_jcl(self._new(None, "proclib", pr["name"]), pr, self.program_paths, proc=True)
        self._link_generated()
        self._link_dependents()
        self._file_edges()
        self._link_collisions()
        self._collisions()
        self._stale_copies()
        self._gaps()
        self._dead()
        self._check_horrors()

    # ------------------------------------------------------------ phase 3 channels
    def _collisions(self) -> None:
        """copy_collisions: an unqualified COPY whose member sits in more than one library of
        the importer's SYSLIB order. The first library wins (as on z/OS); a reader that is
        told the libraries should report the rest as shadowed. One fact per (importer, member),
        at the first such COPY."""
        for m in self.members.values():
            seen: set = set()
            order = self.order_of(m.app, m.path)
            for f in m.facts.get("copies", []):
                if f["kind"] != "copy" or f.get("library") or f["member"] in seen:
                    continue
                found = [(lib, self.copybooks[(lib, f["member"])][0]) for lib in order
                         if (lib, f["member"]) in self.copybooks]
                if len(found) < 2:
                    continue
                seen.add(f["member"])
                if found[0][1] != f["resolves_to"]:
                    raise ValueError(f"{m.path}: COPY {f['member']} resolves to {f['resolves_to']}, SYSLIB to {found[0]}")
                row = {"member": f["member"], "line": f["line"], "library": found[0][0], "resolves_to": found[0][1],
                       "shadowed": [{"library": lib, "path": p} for lib, p in found[1:]]}
                for tag in ("horror", "depends_on"):
                    if f.get(tag):
                        row[tag] = f[tag]
                m.facts.setdefault("copy_collisions", []).append(row)

    def _stale_copies(self) -> None:
        """A call that resolves to a program with a stale copy (a second member holding the same
        PROGRAM-ID, H-0050) must not draw an edge to the copy: an explicit file_edges phantom."""
        for m in self.members.values():
            for f in m.facts.get("call_sites", []):
                pid = (f.get("target") or "").upper()
                for other in self.program_members.get(pid, []):
                    if f.get("resolves_to") and other != f["resolves_to"]:
                        kind = "exec" if f["verb"] == "EXEC PGM" else "call"
                        with m.horror(f.get("horror")):
                            m.phantom("file_edges", kind=kind, target=other,
                                      why=f"{other} holds PROGRAM-ID {pid} too, but {f['verb']} {pid} loads "
                                          f"the program object built from {f['resolves_to']}")

    def _gaps(self) -> None:
        """gaps: a reference to a member the estate should hold and does not (a COPY, a CALL /
        LINK / XCTL, an EXEC PGM, a CSD PROGRAM or TRANSACTION). The reference itself is a
        fact of its own channel with `resolves_to: null`; the gap says that nothing in the
        estate answers it, so a reader must not resolve it to a same-named member of another
        kind. Names the system supplies (SYSTEM_MEMBERS) are not gaps."""
        stems = {Path(p).stem.upper() for p in self.members}

        def add(m: Member, src: dict[str, Any], kind: str, name: str, why: str) -> None:
            if name.upper() in SYSTEM_MEMBERS:
                return
            row = {"kind": kind, "name": name, "line": src["line"], "why": why}
            if name.upper() in stems:
                row["lookalikes"] = sorted(p for p in self.members if Path(p).stem.upper() == name.upper())
            for tag in ("horror", "depends_on"):
                if src.get(tag):
                    row[tag] = src[tag]
            m.facts.setdefault("gaps", []).append(row)

        for m in self.members.values():
            for f in m.facts.get("copies", []):
                if f["resolves_to"] is None:
                    add(m, f, f["kind"], f["member"], "no library in the program's SYSLIB order holds the member")
            for f in m.facts.get("call_sites", []):
                if f["verb"] in ("CALL", "LINK", "XCTL", "EXEC PGM") and f.get("resolves_to") is None:
                    add(m, f, f["verb"].lower().replace("exec pgm", "exec"), f["target"],
                        "no member of the estate holds the program")
            for f in m.facts.get("transactions", []):
                if f.get("resolves_to") is None:
                    add(m, f, "transaction", f["program"], "the transaction's PROGRAM is not in the estate")
            for f in m.facts.get("csd_resources", []):
                if f["type"] == "PROGRAM" and f["name"].upper() not in self.program_paths:
                    add(m, f, "csd-program", f["name"], "DEFINE PROGRAM names a program the estate does not hold")

    def _dead(self) -> None:
        """dead: what nothing in the estate reaches. A program no CALL / LINK / XCTL / EXEC PGM /
        TRANSACTION resolves to, a copybook no COPY resolves to (both declared by the app and
        checked here), and a paragraph no PERFORM / GO TO names and no paragraph falls into
        (recorded and checked by the program writer)."""
        reached = {f.get("resolves_to") for m in self.members.values()
                   for ch in ("call_sites", "transactions", "copies") for f in m.facts.get(ch, [])}
        for app in self.apps:
            a = app["id"]
            for p in app.get("programs", []):
                if not p.get("dead"):
                    continue
                path = member_path(a, "cobol", p["member"])
                if path in reached:
                    raise ValueError(f"{path} is declared dead, but a reference resolves to it")
                m = self.members[path]
                prog = m.facts["programs"][0]
                with m.horror(p.get("dead_horror")):
                    m.fact("dead", kind="program", name=prog["program_id"], line=prog["line"], why=p["dead"])
            for lib, key in (("copybook", "copybooks"), ("oldcopy", "old_copybooks")):
                for cb in app.get(key, []):
                    if not cb.get("orphan"):
                        continue
                    path = member_path(a, lib, cb["member"])
                    if path in reached:
                        raise ValueError(f"{path} is declared an orphan, but a COPY resolves to it")
                    m = self.members[path]
                    with m.horror(cb.get("orphan_horror")):
                        m.fact("dead", kind="copybook", name=cb["member"], line=1, why=cb["orphan"])

    def _link_collisions(self) -> None:
        """#4265 (H-0034): a COPY of a member that exists in more than one library resolves
        right only when the reader follows the program's own SYSLIB order. Every such COPY,
        and the layout that expands it, is marked `depends_on` H-0034 (unless planted there)."""
        libs_of: dict[str, set] = {}
        for (lib, member) in self.copybooks:
            libs_of.setdefault(member, set()).add(lib)
        shared = {mem for mem, libs in libs_of.items() if len(libs) > 1}
        # a phase-3 drift horror owns its own COPYs; H-0034 stays the cascade for the rest
        own = {h for h, d in self.horror_defs.items() if d.get("collision") and h != "H-0034"}
        for m in self.members.values():
            hit = False
            for f in m.facts.get("copies", []):
                if f["member"] in shared and f.get("horror") != "H-0034" and f.get("horror") not in own:
                    f.setdefault("depends_on", ["H-0034"])
                    hit = True
            if not hit:
                continue
            for lay in m.facts.get("layouts", []):
                files = {x["file"] for x in lay["fields"]}
                if (any(p.endswith(f"/{mem}.cpy") for p in files for mem in shared)
                        and lay.get("horror") != "H-0034" and lay.get("horror") not in own):
                    lay.setdefault("depends_on", ["H-0034"])

    def _file_edges(self) -> None:
        """file_edges: the resolved invocation edges between members (edge_data kinds `call`
        for CALL / LINK / XCTL, `exec` for JCL EXEC PGM), one per (target, kind)."""
        for m in self.members.values():
            seen: dict[tuple[str, str], dict[str, Any]] = {}
            for f in m.facts.get("call_sites", []):
                if not f.get("resolves_to") or f["resolves_to"] == m.path:
                    continue
                kind = "exec" if f["verb"] == "EXEC PGM" else "call" if f["verb"] in ("CALL", "LINK", "XCTL") else None
                if kind is None or (f["resolves_to"], kind) in seen:
                    continue
                row = {"kind": kind, "target": f["resolves_to"]}
                for tag in ("horror", "depends_on"):
                    if f.get(tag):
                        row[tag] = f[tag]
                seen[(f["resolves_to"], kind)] = row
            for row in seen.values():
                m.facts.setdefault("file_edges", []).append(row)

    def _link_dependents(self) -> None:
        """A call site whose target program's identity is itself a planted horror (H-0008)
        resolves only once that horror is fixed: mark it `depends_on`, so the scorer can show
        it as that horror's cascade rather than as an unexplained failure."""
        for m in self.members.values():
            for f in m.facts.get("call_sites", []):
                target = self.members.get(f.get("resolves_to") or "")
                tags = sorted({p["horror"] for p in (target.facts.get("programs", []) if target else []) if p.get("horror")})
                if tags and f.get("horror") not in tags:
                    f["depends_on"] = tags

    def _link_generated(self) -> None:
        """A COPY of a generated member (a BMS symbolic map) may also be answered by the member
        it is generated from: the import may name either."""
        for m in self.members.values():
            for f in m.facts.get("copies", []):
                target = self.members.get(f["resolves_to"]) if f["resolves_to"] else None
                if target is not None and target.generated_from:
                    f["alternatives"] = [target.generated_from]

    def _check_horrors(self) -> None:
        used = set().union(*(m.horrors for m in self.members.values()))
        unknown = used - set(self.horror_defs)
        if unknown:
            raise ValueError(f"facts tagged with undefined horrors: {sorted(unknown)}")
        unplanted = [h for h, d in self.horror_defs.items() if h not in used and d.get("planted", True)]
        if unplanted:
            raise ValueError(f"horrors defined but never planted: {unplanted}")

    # ------------------------------------------------------------ output
    def files(self) -> dict[str, bytes]:
        """Every generated file, repo-relative path -> bytes. Deterministic for a given seed/size."""
        out: dict[str, bytes] = {}
        datas = {path: m.data() for path, m in self.members.items()}
        for path in sorted(self.members):
            out[f"estate/{path}"] = datas[path]
        by_app: dict[str, dict[str, Any]] = {}
        manifest_members: dict[str, Any] = {}
        for path, m in sorted(self.members.items()):
            scope = m.app or "_shared"
            by_app.setdefault(scope, {})[path] = m.key_entry()
            manifest_members[path] = {
                "app": m.app,
                "library": m.library,
                "language": m.language,
                "sha256": hashlib.sha256(datas[path]).hexdigest(),
                "bytes": len(datas[path]),
                "encoding": m.encoding,
                "storage": m.storage,
                "key": f"key/apps/{scope}.json",
                "compile": m.compile,
                **({"generated_from": m.generated_from} if m.generated_from else {}),
                **({"horrors": sorted(m.horrors)} if m.horrors else {}),
            }
        for scope, members in sorted(by_app.items()):
            out[f"key/apps/{scope}.json"] = dump({"format": FORMAT, "app": None if scope == "_shared" else scope,
                                                  "members": members})
        totals = {ch: sum(len(m.facts.get(ch, [])) for m in self.members.values()) for ch in CHANNELS}
        totals["phantoms"] = sum(len(m.phantoms) for m in self.members.values())
        out["key/manifest.json"] = dump({
            "format": FORMAT,
            "generator": {"version": VERSION, "seed": self.seed, "size": self.size},
            "estate_root": "estate",
            "apps": [{"id": a["id"], "title": a["title"], "style": a.get("style", "")} for a in self.apps],
            "channels": list(CHANNELS),
            "fact_totals": totals,
            # what a scanner must be told: every member not in UTF-8, by its estate-relative path
            "code_pages": {p: m.encoding for p, m in sorted(self.members.items())
                           if m.encoding not in ("utf-8", "utf-8-sig")},
            # what a scanner must be told about COPY: the libraries and each program's SYSLIB order
            "copy_libraries": self.copy_library_declaration(),
            "horrors": sorted(self.horror_defs),
            "members": manifest_members,
        })
        for hid, d in sorted(self.horror_defs.items()):
            out[f"horrors/{hid}.json"] = dump(self._horror_record(hid, d))
        out["horrors/README.md"] = self._horror_index().encode("utf-8")
        return out

    def copy_library_declaration(self) -> dict[str, Any]:
        """The estate's copy libraries (library-name -> directories) and SYSLIB orders, in the
        shape gitgalaxy's `galaxyscope --copy-libraries` reads: a program's own order first,
        then one per app. Only libraries that hold a member are listed."""
        libraries: dict[str, list[str]] = {}
        for (lib, _member), (path, _items) in sorted(self.copybooks.items()):
            d = path.rsplit("/", 1)[0]
            if d not in libraries.setdefault(lib, []):
                libraries[lib].append(d)
        syslib_rows = [{"programs": path, "order": [n for n in order if n in libraries]}
                       for path, order in sorted(self.program_syslib.items())]
        syslib_rows += [{"programs": f"apps/{a}/*", "order": [n for n in order if n in libraries]}
                        for a, order in sorted(self.app_syslib.items())]
        return {"libraries": dict(sorted(libraries.items())), "syslib": syslib_rows}

    def _horror_record(self, hid: str, d: dict[str, Any]) -> dict[str, Any]:
        planted: list[dict[str, Any]] = []
        for path, m in sorted(self.members.items()):
            if hid not in m.horrors:
                continue
            facts = {ch: [f for f in m.facts.get(ch, []) if f.get("horror") == hid] for ch in CHANNELS}
            planted.append({
                "member": path,
                "compile": m.compile,
                "expected": {ch: v for ch, v in facts.items() if v},
                "phantoms": [p for p in m.phantoms if p.get("horror") == hid],
            })
        return {"format": "estate-crucible-horror/1", **d, "planted": planted}

    def _horror_index(self) -> str:
        rows = ["# Horror catalog", "",
                "Generated by `python3 -m generator`; do not edit. Each `H-*.json` holds the horror's",
                "definition (from `spec/horrors.json`), the members it is planted in, and the expected",
                "facts and phantoms the answer key carries for it. An issue of `realism` marks a horror",
                "that imitates what real customer estates look like rather than a known defect; its",
                "`realism` field says why it is there.", "",
                "| id | issue (defect) | category | title | planted in |", "|---|---|---|---|---|"]
        for hid, d in sorted(self.horror_defs.items()):
            where = ", ".join(f"`{p}`" for p, m in sorted(self.members.items()) if hid in m.horrors)
            issue = f"[#{d['issue']}](https://github.com/squid-protocol/gitgalaxy/issues/{d['issue']})" if d.get("issue") else ""
            src = f"{issue} ({d['defect']})" if d.get("defect") else issue
            if d.get("realism"):
                src = "realism"
            rows.append(f"| {hid} | {src} | {d['category']} | {d['title']} | {where} |")
        if self.not_planted:
            rows += ["", "## Field-testing defects not planted", "",
                     "From gitgalaxy `tests/cobol_mainframe/field_testing.json`; each waits for what the reason names.", "",
                     "| defects | why not |", "|---|---|"]
            for np in self.not_planted:
                rows.append(f"| {', '.join(np['defects'])} | {np['why']} |")
        return "\n".join(rows) + "\n"


def dump(obj: Any) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8")


def write_tree(files: dict[str, bytes], root: Path) -> None:
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
