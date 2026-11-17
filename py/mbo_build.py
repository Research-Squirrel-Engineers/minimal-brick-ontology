"""Describe a brick build in RDF with the Minimal Brick Ontology.

Library + CLI. A build spec is plain JSON, so a reconstruction workflow (for
example a KIRI scan reconstruction that already writes aenderungen.json) can
emit it directly:

{
  "id": "pyramid-white",                      # becomes https://w3id.org/mbo/example/<id>
  "label": "Stepped white pyramid",
  "scale": 0.6667,                             # optional scene scale of the digital model
  "layerHeightPlates": 3,                      # optional, default 3 (one brick)
  "source": "user-chat-pyramid",               # optional id from data/seed/sources.csv
  "scan": {"label": "KIRI Engine SfM scan"},   # optional: adds a CRMdig derivation
  "layers": [ {"index": 0, "pieces": [
      {"part": "3001", "colour": "white", "x": 0, "y": 0, "rot": 0} ]} ],
  "assemblies": [ {"id": "minifig-1", "type": "Minifigure", "label": "...",
      "pieces": [ {"part": "3626", "colour": "yellow"} ]} ]
}

Positions are in studs (x, y) and plate heights (z). `rot` 0 means the design's
length runs along X. Overlaps inside a layer are rejected.

Usage: python py/mbo_build.py spec.json out.ttl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD

import mbo_utils as U

MBO = Namespace(U.NS["mbo"])
MBOT = Namespace(U.NS["mbot"])
MBOX = Namespace(U.NS["mbox"])
MBOS = Namespace(U.NS["mbos"])
CRMDIG = Namespace(U.NS["crmdig"])


def _catalogue():
    import step_thesaurus as T
    rep: list[str] = []
    colours = {c["slug"] for c in T.load_colours(rep)}
    parts = {p["num"]: p for p in T.load_parts(rep)}
    return colours, parts


def check_spec(spec: dict, colours: set[str], parts: dict) -> list[str]:
    errors: list[str] = []
    refs = [p for l in spec.get("layers", []) for p in l["pieces"]]
    refs += [p for a in spec.get("assemblies", []) for p in a["pieces"]]
    for p in refs:
        if p["part"] not in parts:
            errors.append(f"unknown part {p['part']!r}")
        if U.slug(p["colour"]) not in colours:
            errors.append(f"unknown colour {p['colour']!r}")
    for layer in spec.get("layers", []):
        occ: dict[tuple[int, int], int] = {}
        for n, p in enumerate(layer["pieces"]):
            part = parts.get(p["part"])
            if not part or not part["length"] or float(p.get("rot", 0)) % 90:
                continue
            L, W = int(part["length"]), int(part["width"])
            if int(float(p.get("rot", 0)) // 90) % 2:
                L, W = W, L
            for dx in range(L):
                for dy in range(W):
                    cell = (p["x"] + dx, p["y"] + dy)
                    if cell in occ:
                        errors.append(f"layer {layer['index']}: piece {n} overlaps piece {occ[cell]} at {cell}")
                    occ[cell] = n
    return errors


def element_iri(part: str, colour: str) -> URIRef:
    return MBOX[f"element/{part}-{U.slug(colour)}"]


def export_build(spec: dict, check: bool = True) -> Graph:
    colours, parts = _catalogue()
    if check:
        errs = check_spec(spec, colours, parts)
        if errs:
            raise ValueError("invalid build spec:\n  " + "\n  ".join(errs[:20]))
    g = Graph()
    bid = spec["id"]
    build = MBOX[bid]
    lh = int(spec.get("layerHeightPlates", 3))
    elements: set[tuple[str, str]] = set()

    def piece(iri: URIRef, p: dict) -> None:
        g.add((iri, RDF.type, MBO.Piece))
        g.add((iri, MBO.instanceOfElement, element_iri(p["part"], p["colour"])))
        elements.add((p["part"], U.slug(p["colour"])))

    g.add((build, RDF.type, MBO.Build))
    g.add((build, RDFS.label, Literal(spec.get("label", bid), lang="en")))
    if spec.get("description"):
        g.add((build, DCTERMS.description, Literal(spec["description"], lang="en")))
    if spec.get("source"):
        g.add((build, DCTERMS.source, MBOS[spec["source"]]))
    n = 0
    for layer in sorted(spec.get("layers", []), key=lambda l: l["index"]):
        li = MBOX[f"{bid}/layer/{layer['index']}"]
        g.add((li, RDF.type, MBO.Layer))
        g.add((li, MBO.layerIndex, Literal(layer["index"])))
        g.add((li, MBO.isLayerOf, build))
        g.add((build, MBO.hasLayer, li))
        g.add((li, RDFS.label, Literal(f"Layer {layer['index']}", lang="en")))
        for p in layer["pieces"]:
            n += 1
            pi = MBOX[f"{bid}/piece/{n}"]
            piece(pi, p)
            g.add((pi, MBO.gridX, Literal(int(p["x"]))))
            g.add((pi, MBO.gridY, Literal(int(p["y"]))))
            g.add((pi, MBO.gridZ, Literal(int(p.get("z", layer["index"] * lh)))))
            g.add((pi, MBO.rotationDegrees, Literal(str(p.get("rot", 0)), datatype=XSD.decimal)))
            g.add((pi, MBO.inLayer, li))
            g.add((li, MBO.hasPiece, pi))
    for a in spec.get("assemblies", []):
        ai = MBOX[f"{bid}/{a['id']}"]
        g.add((ai, RDF.type, MBO.Minifigure if a.get("type") == "Minifigure" else MBO.Assembly))
        g.add((ai, RDFS.label, Literal(a.get("label", a["id"]), lang="en")))
        for k, p in enumerate(a["pieces"], 1):
            pi = MBOX[f"{bid}/{a['id']}/piece/{k}"]
            piece(pi, p)
            g.add((ai, MBO.hasPiece, pi))
    for part, col in sorted(elements):
        e = MBOX[f"element/{part}-{col}"]
        g.add((e, RDF.type, MBO.Element))
        g.add((e, MBO.hasDesign, MBOT[f"part/{part}"]))
        g.add((e, MBO.hasColour, MBOT[f"colour/{col}"]))
        g.add((e, RDFS.label, Literal(f"{parts[part]['name']}, {col}", lang="en")))
    if spec.get("scan"):
        scan, model, proc = MBOX[f"{bid}/scan"], MBOX[f"{bid}/model"], MBOX[f"{bid}/reconstruction"]
        g.add((scan, RDF.type, CRMDIG.D1_Digital_Object))
        g.add((scan, RDFS.label, Literal(spec["scan"].get("label", "Scan"), lang="en")))
        g.add((model, RDF.type, MBO.BuildModel))
        g.add((model, RDFS.label, Literal(f"Brick model of {spec.get('label', bid)}", lang="en")))
        g.add((model, MBO.describesBuild, build))
        if spec.get("scale"):
            g.add((model, MBO.sceneScale, Literal(str(spec["scale"]), datatype=XSD.decimal)))
        g.add((proc, RDF.type, MBO.ReconstructionProcess))
        g.add((proc, RDFS.label, Literal("Reconstruction from scan", lang="en")))
        g.add((proc, CRMDIG.L21_used_as_derivation_source, scan))
        g.add((proc, CRMDIG.L22_created_derivative, model))
    return g


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    g = export_build(spec)
    n = U.write_turtle(g, Path(argv[2]))
    print(f"wrote {argv[2]}: {n} triples")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
