"""Shared constants, paths and canonical writers for minimal-brick-ontology.

No clock is used anywhere: dates come from RELEASE, so a rebuild of unchanged
data is byte-identical.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

RELEASE = "2026-11-18"          # date of the vocabulary release, not of the run
VERSION = "0.1.0"
REPO = "minimal-brick-ontology"
PAGES = "https://research-squirrel-engineers.github.io/minimal-brick-ontology/"
GITHUB = "https://github.com/Research-Squirrel-Engineers/minimal-brick-ontology"

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = DATA / "seed"
RAW = DATA / "raw" / "rebrickable"
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
ONTOLOGY = ROOT / "ontology"
SHAPES = ROOT / "shapes"

# Namespaces (see PRIMER.md A6 for the IRI map)
NS = {
    "mbo": "https://w3id.org/mbo/ontology#",
    "mbot": "https://w3id.org/mbo/thesaurus/",
    "mbox": "https://w3id.org/mbo/example/",
    "mbos": "https://w3id.org/mbo/source/",
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "crmba": "http://www.cidoc-crm.org/extensions/crmba/",
    "crmdig": "http://www.cidoc-crm.org/extensions/crmdig/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dct": "http://purl.org/dc/terms/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "sh": "http://www.w3.org/ns/shacl#",
}

_LOCAL = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")


def ensure_dirs() -> None:
    for d in (DIST, DOCS, DOCS / "assets", RAW):
        d.mkdir(parents=True, exist_ok=True)


def slug(text: str) -> str:
    """Stable URL slug: lower case, 'grey' spelled 'gray', non-alphanumerics to '-'."""
    t = text.lower().replace("grey", "gray")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t


def norm(text: str) -> str:
    """Matching key for colour names across sources."""
    return re.sub(r"[^a-z0-9]", "", text.lower().replace("grey", "gray"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def write_json(path: Path, obj) -> None:
    write_text(path, json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False))


# ---------------------------------------------------------------- Turtle ---

def _qname(uri: str, prefixes: dict[str, str]) -> str:
    best = None
    for p, ns in prefixes.items():
        if uri.startswith(ns):
            local = uri[len(ns):]
            if local == "" or _LOCAL.match(local):
                if best is None or len(ns) > len(prefixes[best[0]]):
                    best = (p, local)
    return f"{best[0]}:{best[1]}" if best else f"<{uri}>"


def _esc(s: str) -> str:
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))


def _term(t, prefixes) -> str:
    if isinstance(t, URIRef):
        return _qname(str(t), prefixes)
    if isinstance(t, Literal):
        body = f'"{_esc(str(t))}"'
        if t.language:
            return f"{body}@{t.language}"
        if t.datatype and t.datatype != XSD.string:
            return f"{body}^^{_qname(str(t.datatype), prefixes)}"
        return body
    raise ValueError(f"blank nodes are not allowed in generated graphs: {t!r}")


def _okey(o):
    if isinstance(o, Literal):
        return (1, str(o), o.language or "", str(o.datatype or ""))
    return (0, str(o), "", "")


def write_turtle(g: Graph, path: Path, prefixes: dict[str, str] | None = None) -> int:
    """Deterministic Turtle: sorted prefixes, subjects, predicates and objects."""
    prefixes = prefixes or NS
    used = {}
    lines = []
    subjects = sorted(set(g.subjects()), key=str)
    body = []
    for s in subjects:
        preds = sorted(set(g.predicates(s)), key=lambda p: (p != RDF.type, str(p)))
        chunks = []
        for p in preds:
            objs = sorted(set(g.objects(s, p)), key=_okey)
            pt = "a" if p == RDF.type else _term(p, prefixes)
            chunks.append(f"    {pt} " + ", ".join(_term(o, prefixes) for o in objs))
        body.append(_term(s, prefixes) + "\n" + " ;\n".join(chunks) + " .\n")
    text_body = "\n".join(body)
    for p, ns in sorted(prefixes.items()):
        if f"{p}:" in text_body or f"<{ns}" in text_body:
            used[p] = ns
    for p, ns in sorted(used.items()):
        lines.append(f"@prefix {p}: <{ns}> .")
    write_text(path, "\n".join(lines) + "\n\n" + text_body)
    return len(g)


def read_turtle(path: Path) -> Graph:
    g = Graph()
    g.parse(path, format="turtle")
    return g


def read_csv(path: Path) -> list[dict]:
    import csv
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))
