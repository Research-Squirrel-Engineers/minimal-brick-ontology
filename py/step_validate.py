"""Validate everything: parse, vocabulary closure, SHACL (MBO shapes and DCAT-AP subset).

Writes dist/validation_report.txt. Exit code 1 on any violation (warnings are
reported but do not fail). Run standalone: python py/step_validate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyshacl import validate
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF

import mbo_utils as U

MBO = U.NS["mbo"]


def mbo_terms(g: Graph) -> set[str]:
    out = set()
    for s, p, o in g:
        for t in (p, o if not isinstance(o, __import__("rdflib").Literal) else None, s if p == RDF.type else None):
            if t is not None and str(t).startswith(MBO):
                out.add(str(t))
    return out


def main() -> int:
    lines: list[str] = []
    ok = True
    graphs = {}
    for label, path in [("ontology", U.ONTOLOGY / "mbo.ttl"), ("thesaurus", U.DIST / "thesaurus.ttl"),
                        ("example", U.DIST / "example-pyramid.ttl"), ("catalogue", U.DIST / "catalogue.ttl"),
                        ("mbo-shapes", U.SHAPES / "mbo-shapes.ttl"), ("dcat-ap-subset", U.SHAPES / "dcat-ap-subset-shapes.ttl")]:
        g = U.read_turtle(path)
        graphs[label] = g
        lines.append(f"parse   {label:<15} {len(g):>8} triples  ({path.relative_to(U.ROOT).as_posix()})")

    onto = graphs["ontology"]
    declared = {str(s) for s in onto.subjects() if str(s).startswith(MBO)}
    used = mbo_terms(graphs["thesaurus"]) | mbo_terms(graphs["example"])
    undeclared = sorted(t for t in used if t not in declared)
    lines.append(f"closure ontology declares {len(declared)} terms; thesaurus and example use {len(used)}; undeclared: {len(undeclared)}")
    for t in undeclared:
        lines.append(f"  UNDECLARED {t}")
        ok = False

    data = graphs["thesaurus"] + graphs["example"]
    conforms, _g, text = validate(data, shacl_graph=graphs["mbo-shapes"], inference="none", allow_warnings=True)
    lines.append(f"shacl   MBO shapes on thesaurus + example: conforms={conforms}")
    if not conforms:
        ok = False
        lines.append(text[:4000])

    conforms2, rg, text2 = validate(graphs["catalogue"], shacl_graph=graphs["dcat-ap-subset"], inference="none", allow_warnings=True)
    SH = Namespace("http://www.w3.org/ns/shacl#")
    warnings = sum(1 for _ in rg.subjects(SH.resultSeverity, SH.Warning))
    lines.append(f"shacl   DCAT-AP subset on catalogue: conforms={conforms2}, warnings={warnings}")
    if not conforms2:
        ok = False
        lines.append(text2[:4000])
    if warnings and __import__("os").environ.get("MBO_STRICT"):
        lines.append(f"strict  {warnings} DCAT-AP warnings treated as errors")
        ok = False
    lines.append("note    the DCAT-AP check is a hand-written subset; run the official DCAT-AP shapes before submitting to a portal")
    lines.append("RESULT  " + ("OK" if ok else "FAILED"))
    U.write_text(U.DIST / "validation_report.txt", "\n".join(lines))
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
