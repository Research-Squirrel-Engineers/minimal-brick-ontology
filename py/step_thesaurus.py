"""Build the SKOS thesaurus (colours, parts, features, units, identifier systems).

Inputs : data/seed/*.csv (always) and data/raw/rebrickable/*.csv (optional,
         produced by `python main.py fetch`)
Outputs: dist/thesaurus.ttl, dist/colours.csv, dist/thesaurus.json

Every concept carries dct:source links and an mbo:verification status.
Runs offline. Run standalone: python py/step_thesaurus.py
"""
from __future__ import annotations

import colorsys
import csv
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS, XSD

import mbo_utils as U

MBO = Namespace(U.NS["mbo"])
MBOT = Namespace(U.NS["mbot"])
MBOS = Namespace(U.NS["mbos"])

SCHEMES = {
    "colour": ("Colours", "Farben", "LEGO colours with names, identifiers, hex approximations and finish groups.", MBO.Colour),
    "part": ("Parts", "Bauteile", "Bricks, plates, tiles, baseplates and minifigure parts, grouped by category.", MBO.ElementDesign),
    "feature": ("Features", "Merkmale", "Geometric and connective features of parts.", MBO.Feature),
    "unit": ("Units", "Einheiten", "Grid and measurement units of the brick system.", MBO.Unit),
    "identifier-system": ("Identifier systems", "Nummernsysteme", "Numbering systems used for parts.", MBO.IdentifierSystem),
}
VOCAB_TYPE = {"colour": MBO.ColourGroup, "part": MBO.PartCategory, "feature": MBO.Feature,
              "unit": MBO.Unit, "identifier-system": MBO.IdentifierSystem}

SKIP_PRINT = re.compile(r"(pr|pb)\d")          # printed variants are out of scope
DIMS = re.compile(r"^(Brick|Plate|Tile|Baseplate) (\d+) x (\d+)$")
RB_TOP = [(re.compile(r"^Bricks?\b"), "brick"), (re.compile(r"^Plates?\b"), "plate"),
          (re.compile(r"^Tiles?\b"), "tile"), (re.compile(r"^Baseplates?\b"), "baseplate")]
RB_MINIFIG = [(re.compile(r"^Minifig Heads"), "minifig-head"), (re.compile(r"^Minifig Torsos"), "minifig-torso"),
              (re.compile(r"^Minifig Arms"), "minifig-arm"), (re.compile(r"^Minifig Hands"), "minifig-hand"),
              (re.compile(r"^Minifig Headwear"), "minifig-headwear")]


# ------------------------------------------------------------------ rules ---

def finish_of(name: str, is_trans: bool) -> str:
    n = name.lower()
    if is_trans or n.startswith("trans"):
        return "transparent"
    if any(k in n for k in ("metallic", "pearl", "chrome", "flat silver", "flat dark gold")):
        return "metallic"
    if any(k in n for k in ("glitter", "speckle", "milky", "glow", "satin", "opal", "neon")):
        return "special"
    return "solid"


def hue_family(hexs: str) -> str | None:
    """Coarse family from a hex value. A heuristic of this repository, not a LEGO classification."""
    if not hexs or not re.fullmatch(r"[0-9A-Fa-f]{6}", hexs):
        return None
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    H = h * 360
    if l > 0.93:
        return "White"
    if l < 0.10:
        return "Black"
    if s < 0.12:
        return "Grey"
    if 10 <= H < 50 and l < 0.35:
        return "Brown"
    if 25 <= H < 55 and l >= 0.6 and s < 0.75:
        return "Tan"
    if H < 15 or H >= 345:
        return "Red"
    if H < 45:
        return "Orange"
    if H < 70:
        return "Yellow"
    if H < 165:
        return "Green"
    if H < 200:
        return "Turquoise"
    if H < 255:
        return "Blue"
    if H < 290:
        return "Purple"
    return "Pink"


# ---------------------------------------------------------------- loading ---

def load_sources() -> dict[str, dict]:
    rows = U.read_csv(U.SEED / "sources.csv")
    return {r["id"]: r for r in rows}


def split(s: str) -> list[str]:
    return [x for x in (s or "").split("|") if x]


def load_colours(report: list[str]) -> list[dict]:
    recs: list[dict] = []
    index: dict[str, dict] = {}
    for r in U.read_csv(U.SEED / "colours_seed.csv"):
        rec = {
            "name": r["name"], "alt": split(r["alt_labels"]), "lego_id": r["lego_id"], "gobricks_id": r["gobricks_id"],
            "finish": r["finish"], "era": r["era"], "hex": r["hex"].upper(), "hex_status": r["hex_status"],
            "sources": split(r["sources"]), "note": r["note"], "rb_id": "", "verification": "sourced" if any(x != "seed-unverified" for x in split(r["sources"])) else "seed",
        }
        if not rec["hex"]:
            rec["hex_status"] = "none"
        recs.append(rec)
        for k in [rec["name"], *rec["alt"]]:
            index.setdefault(U.norm(k), rec)

    path = U.RAW / "colors.csv"
    if path.exists():
        matched = created = 0
        for r in U.read_csv(path):
            name = r["name"]
            if name.startswith("[") or int(r["id"]) < 0 or r["id"] == "9999":
                continue
            is_trans = r.get("is_trans", "").lower() in ("t", "true", "1")
            rec = index.get(U.norm(name))
            if rec:
                matched += 1
            else:
                created += 1
                rec = {"name": name, "alt": [], "lego_id": "", "gobricks_id": "", "finish": finish_of(name, is_trans),
                       "era": "", "hex": "", "hex_status": "none", "sources": [], "note": "", "rb_id": "", "verification": "rebrickable"}
                recs.append(rec)
                index[U.norm(name)] = rec
            rec["rb_id"] = r["id"]
            rb_hex = (r.get("rgb") or "").upper()
            if rb_hex:
                if rec["hex"] and rec["hex"] != rb_hex:
                    rec["note"] = (rec["note"] + " " if rec["note"] else "") + f"Seed hex {rec['hex']} replaced by Rebrickable hex {rb_hex}."
                rec["hex"], rec["hex_status"] = rb_hex, "rebrickable"
            if "rebrickable-downloads" not in rec["sources"]:
                rec["sources"].append("rebrickable-downloads")
            if rec["verification"] == "seed" and "seed-unverified" in rec["sources"] and rb_hex:
                rec["sources"] = [s for s in rec["sources"] if s != "seed-unverified"]
                rec["verification"] = "sourced"
        report.append(f"colours: {matched} Rebrickable rows matched seed colours, {created} added")
    else:
        report.append("colours: seed only (no data/raw/rebrickable/colors.csv; run `python main.py fetch`)")
    # unique slugs
    seen: dict[str, int] = {}
    for rec in recs:
        s = U.slug(rec["name"])
        if s in seen:
            s = f"{s}-{rec['rb_id'] or rec['lego_id'] or seen[s]}"
        seen[s] = seen.get(s, 0) + 1
        rec["slug"] = s
    return recs


def load_parts(report: list[str]) -> list[dict]:
    parts: dict[str, dict] = {}
    for r in U.read_csv(U.SEED / "parts_seed.csv"):
        parts[r["part_num"]] = {
            "num": r["part_num"], "name": r["name"], "category": r["category"],
            "length": r["studs_length"], "width": r["studs_width"], "height": r["height_plates"],
            "design_id": r["design_id"], "bricklink": r["bricklink_id"], "ldraw": r["ldraw_id"],
            "status": "sourced" if r["id_status"] == "sourced" else "seed", "sources": split(r["sources"]),
            "note": r["note"], "rb_cat": "", "rb_num": "",
        }
    pp, pc = U.RAW / "parts.csv", U.RAW / "part_categories.csv"
    if pp.exists() and pc.exists():
        cats = {r["id"]: r["name"] for r in U.read_csv(pc)}
        confirmed = added = skipped = 0
        for r in U.read_csv(pp):
            num, name, cat = r["part_num"], r["name"], cats.get(r["part_cat_id"], "")
            top = next((t for rx, t in RB_TOP if rx.match(cat)), None)
            if top is None:
                top = next((t for rx, t in RB_MINIFIG if rx.match(cat)), None)
                if top is None and cat.startswith("Minifig Hips and Legs"):
                    top = "minifig-leg" if "leg" in name.lower() else "minifig-hips"
            if top is None:
                continue
            if SKIP_PRINT.search(num):
                skipped += 1
                continue
            p = parts.get(num)
            if p:
                confirmed += 1
                p["status"] = "rebrickable"
                p["sources"] = [s for s in p["sources"] if s != "seed-unverified"] + ["rebrickable-downloads"]
            else:
                added += 1
                p = {"num": num, "name": name, "category": top, "length": "", "width": "", "height": "", "design_id": "",
                     "bricklink": "", "ldraw": "", "status": "rebrickable", "sources": ["rebrickable-downloads"], "note": "",
                     "rb_cat": "", "rb_num": ""}
                m = DIMS.match(name)
                if m:
                    a, b = int(m.group(2)), int(m.group(3))
                    p["length"], p["width"] = str(max(a, b)), str(min(a, b))
                    p["height"] = {"Brick": "3", "Plate": "1", "Tile": "1", "Baseplate": ""}[m.group(1)]
                parts[num] = p
            p["rb_num"] = num
            p["rb_cat"] = cat
        report.append(f"parts: {confirmed} seed parts confirmed in Rebrickable, {added} added, {skipped} printed variants skipped")
        missing = [n for n, p in parts.items() if p["status"] == "seed"]
        if missing:
            report.append(f"parts: {len(missing)} seed parts not found in parts.csv: " + ", ".join(sorted(missing)[:12]))
    else:
        report.append("parts: seed only (no parts.csv / part_categories.csv; run `python main.py fetch`)")
    return sorted(parts.values(), key=lambda p: (p["category"], p["num"]))


# --------------------------------------------------------------- building ---

def build(report: list[str]):
    g = Graph()
    sources = load_sources()
    js = {"release": U.RELEASE, "version": U.VERSION, "schemes": [], "concepts": {}, "sources": {}}
    used_sources: set[str] = set()

    def cid_iri(cid: str) -> URIRef:
        return MBOT[cid]

    def concept(cid, scheme, types, label_en, label_de="", alt=(), definition="", note="", src=(), verification="", extra=None):
        s = cid_iri(cid)
        g.add((s, RDF.type, SKOS.Concept))
        for t in types:
            g.add((s, RDF.type, t))
        g.add((s, SKOS.inScheme, MBOT[scheme]))
        g.add((s, SKOS.prefLabel, Literal(label_en, lang="en")))
        if label_de:
            g.add((s, SKOS.prefLabel, Literal(label_de, lang="de")))
        for a in alt:
            g.add((s, SKOS.altLabel, Literal(a, lang="en")))
        if definition:
            g.add((s, SKOS.definition, Literal(definition, lang="en")))
        if note:
            g.add((s, SKOS.note, Literal(note, lang="en")))
        for sid in src:
            if sid not in sources:
                raise SystemExit(f"unknown source id {sid!r} on {cid}")
            g.add((s, DCTERMS.source, MBOS[sid]))
            used_sources.add(sid)
        if verification:
            g.add((s, MBO.verification, Literal(verification)))
        js["concepts"][cid] = {"id": cid, "scheme": scheme, "iri": str(s), "label": label_en, "labelDe": label_de,
                               "alt": list(alt), "definition": definition, "note": note, "sources": list(src),
                               "verification": verification, "broader": [], "narrower": [], "props": [], "hex": ""}
        if extra:
            js["concepts"][cid].update(extra)
        return s

    def link(child: str, parent: str):
        g.add((cid_iri(child), SKOS.broader, cid_iri(parent)))
        g.add((cid_iri(parent), SKOS.narrower, cid_iri(child)))
        js["concepts"][child]["broader"].append(parent)
        js["concepts"][parent]["narrower"].append(child)

    def prop(cid, label, value):
        if value not in ("", None):
            js["concepts"][cid]["props"].append([label, str(value)])

    tops: dict[str, list[str]] = {k: [] for k in SCHEMES}

    # schemes
    for sk, (en, de, desc, _t) in SCHEMES.items():
        s = MBOT[sk]
        g.add((s, RDF.type, SKOS.ConceptScheme))
        g.add((s, SKOS.prefLabel, Literal(en, lang="en")))
        g.add((s, SKOS.prefLabel, Literal(de, lang="de")))
        g.add((s, DCTERMS.description, Literal(desc, lang="en")))
        g.add((s, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
        g.add((s, DCTERMS.issued, Literal(U.RELEASE, datatype=XSD.date)))
        g.add((s, DCTERMS.modified, Literal(U.RELEASE, datatype=XSD.date)))
        g.add((s, DCTERMS.creator, Literal("Research Squirrel Engineers")))

    # vocab.csv: categories, features, units, identifier systems, colour groups
    vocab = U.read_csv(U.SEED / "vocab.csv")
    for r in vocab:
        sk = r["scheme"]
        cid = f"{sk}/{r['slug']}"
        src = split(r["sources"])
        ver = "seed" if src == ["seed-unverified"] else "sourced"
        concept(cid, sk, [VOCAB_TYPE[sk]], r["label_en"], r["label_de"], definition=r["definition"], note=r["note"], src=src, verification=ver)
        if r["value_mm"]:
            g.add((cid_iri(cid), MBO.nominalMm, Literal(Decimal(r["value_mm"]), datatype=XSD.decimal)))
            prop(cid, "Nominal value (mm)", r["value_mm"])
    for r in vocab:
        cid = f"{r['scheme']}/{r['slug']}"
        if r["parent"]:
            link(cid, f"{r['scheme']}/{r['parent']}")
        else:
            tops[r["scheme"]].append(cid)

    # colours
    colours = load_colours(report)
    with open(U.DIST / "colours.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["slug", "name", "hex", "hex_status", "finish", "hue_family", "lego_id", "rebrickable_id", "gobricks_id", "verification", "iri"])
        for rec in sorted(colours, key=lambda x: x["slug"]):
            cid = f"colour/{rec['slug']}"
            fam = hue_family(rec["hex"])
            src = rec["sources"] or ["seed-unverified"]
            concept(cid, "colour", [MBO.Colour], rec["name"], alt=rec["alt"], note=rec["note"], src=src,
                    verification=rec["verification"], extra={"hex": rec["hex"]})
            s = cid_iri(cid)
            if rec["hex"]:
                g.add((s, MBO.hexColour, Literal(rec["hex"])))
                prop(cid, "Hex", "#" + rec["hex"])
                prop(cid, "Hex status", rec["hex_status"])
            if fam:
                g.add((s, MBO.hueFamily, Literal(fam)))
                prop(cid, "Hue family (derived)", fam)
            for key, pr, lab in (("lego_id", MBO.legoColourId, "LEGO colour ID"), ("rb_id", MBO.rebrickableColourId, "Rebrickable colour ID"),
                                 ("gobricks_id", MBO.gobricksColourId, "Gobricks colour ID"), ("era", MBO.era, "Era")):
                if rec[key]:
                    g.add((s, pr, Literal(rec[key])))
                    prop(cid, lab, rec[key])
            link(cid, f"colour/group-{rec['finish']}")
            w.writerow([rec["slug"], rec["name"], rec["hex"], rec["hex_status"], rec["finish"], fam or "", rec["lego_id"], rec["rb_id"],
                        rec["gobricks_id"], rec["verification"], str(s)])

    # parts
    parts = load_parts(report)
    rb_cat_seen: set[str] = set()
    for p in parts:
        cid = f"part/{p['num']}"
        src = p["sources"] or ["seed-unverified"]
        concept(cid, "part", [MBO.ElementDesign], p["name"], note=p["note"], src=src,
                verification={"seed": "seed", "sourced": "sourced", "rebrickable": "rebrickable"}[p["status"]])
        s = cid_iri(cid)
        g.add((s, SKOS.notation, Literal(p["num"])))
        prop(cid, "Part number", p["num"])
        if p["design_id"]:
            g.add((s, MBO.designId, Literal(p["design_id"])))
            prop(cid, "LEGO design ID", p["design_id"])
        if p["bricklink"]:
            g.add((s, MBO.brickLinkId, Literal(p["bricklink"])))
            prop(cid, "BrickLink part number", p["bricklink"])
        if p["ldraw"]:
            g.add((s, MBO.ldrawId, Literal(p["ldraw"])))
            prop(cid, "LDraw part number", p["ldraw"])
        if p["rb_num"] or p["status"] == "sourced":
            g.add((s, MBO.rebrickablePartNumber, Literal(p["rb_num"] or p["num"])))
            prop(cid, "Rebrickable part number", p["rb_num"] or p["num"])
        if p["length"]:
            L, W = int(p["length"]), int(p["width"])
            g.add((s, MBO.studsLength, Literal(L)))
            g.add((s, MBO.studsWidth, Literal(W)))
            g.add((s, MBO.nominalLengthMm, Literal(Decimal(8) * L - Decimal("0.2"), datatype=XSD.decimal)))
            g.add((s, MBO.nominalWidthMm, Literal(Decimal(8) * W - Decimal("0.2"), datatype=XSD.decimal)))
            prop(cid, "Studs (length x width)", f"{L} x {W}")
            prop(cid, "Nominal footprint (mm, derived)", f"{Decimal(8) * L - Decimal('0.2')} x {Decimal(8) * W - Decimal('0.2')}")
            if p["height"]:
                H = int(p["height"])
                g.add((s, MBO.heightInPlates, Literal(H)))
                g.add((s, MBO.nominalHeightMm, Literal(Decimal("3.2") * H, datatype=XSD.decimal)))
                prop(cid, "Height in plates", H)
                prop(cid, "Nominal height without stud (mm, derived)", Decimal("3.2") * H)
        if p["category"] in ("brick", "plate", "baseplate"):
            g.add((s, MBO.hasFeature, MBOT["feature/stud"]))
        if p["rb_cat"]:
            prop(cid, "Rebrickable category", p["rb_cat"])
        # hierarchy: top category, optionally via the Rebrickable category
        top = p["category"]
        if p["rb_cat"] and top in ("brick", "plate", "tile"):
            rc = f"part/cat-{U.slug(p['rb_cat'])}"
            if rc not in rb_cat_seen:
                rb_cat_seen.add(rc)
                concept(rc, "part", [MBO.PartCategory], p["rb_cat"], note="Rebrickable category.", src=["rebrickable-downloads"], verification="rebrickable")
                link(rc, f"part/{top}")
            link(cid, rc)
        else:
            link(cid, f"part/{top}")

    # top concepts
    for sk, ids in tops.items():
        for cid in sorted(ids):
            g.add((MBOT[sk], SKOS.hasTopConcept, cid_iri(cid)))
            g.add((cid_iri(cid), SKOS.topConceptOf, MBOT[sk]))
    for sk, (en, de, desc, _t) in SCHEMES.items():
        js["schemes"].append({"id": sk, "label": en, "labelDe": de, "description": desc, "iri": str(MBOT[sk]), "top": sorted(tops[sk])})

    # sources as bibliographic resources
    for sid in sorted(used_sources):
        r = sources[sid]
        s = MBOS[sid]
        g.add((s, RDF.type, DCTERMS.BibliographicResource))
        g.add((s, DCTERMS.title, Literal(r["title"], lang="en")))
        g.add((s, RDFS.seeAlso, URIRef(r["url"])))
        g.add((s, DCTERMS.type, Literal(r["kind"])))
        if r["note"]:
            g.add((s, RDFS.comment, Literal(r["note"], lang="en")))
        js["sources"][sid] = {"id": sid, "title": r["title"], "url": r["url"], "kind": r["kind"], "note": r["note"]}

    for c in js["concepts"].values():
        c["narrower"].sort(key=lambda x: (js["concepts"][x]["label"].lower(), x))
    return g, js


def main() -> int:
    U.ensure_dirs()
    report: list[str] = []
    g, js = build(report)
    n = U.write_turtle(g, U.DIST / "thesaurus.ttl")
    U.write_text(U.DIST / "thesaurus.json", __import__("json").dumps(js, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    for line in report:
        print(line)
    by_scheme = {}
    for c in js["concepts"].values():
        by_scheme[c["scheme"]] = by_scheme.get(c["scheme"], 0) + 1
    print(f"thesaurus: {n} triples, " + ", ".join(f"{k}={v}" for k, v in sorted(by_scheme.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
