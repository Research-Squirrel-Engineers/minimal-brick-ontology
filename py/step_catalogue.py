"""Write the DCAT-AP catalogue (dist/catalogue.ttl) describing the datasets.

Distributions point at the GitHub Pages copies that py/step_docs.py publishes.
Dates come from RELEASE. Run standalone: python py/step_catalogue.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, XSD

import mbo_utils as U

DCAT = Namespace(U.NS["dcat"])
CC_BY = URIRef("https://creativecommons.org/licenses/by/4.0/")
ENG = URIRef("http://publications.europa.eu/resource/authority/language/ENG")
PUBLIC = URIRef("http://publications.europa.eu/resource/authority/access-right/PUBLIC")
TTL_FMT = URIRef("http://publications.europa.eu/resource/authority/file-type/RDF_TURTLE")
CSV_FMT = URIRef("http://publications.europa.eu/resource/authority/file-type/CSV")
JSON_FMT = URIRef("http://publications.europa.eu/resource/authority/file-type/JSON")
TTL_MT = URIRef("http://www.iana.org/assignments/media-types/text/turtle")
CSV_MT = URIRef("http://www.iana.org/assignments/media-types/text/csv")
JSON_MT = URIRef("http://www.iana.org/assignments/media-types/application/json")

DATASETS = [
    ("ontology", "Minimal Brick Ontology (OWL)",
     "Small OWL ontology for bricks, plates, tiles, minifigure parts and models built from them, aligned to CIDOC CRM, CRMba and CRMdig.",
     ["ontology", "CIDOC CRM", "building bricks", "OWL"], "ontology.html", [("ontology.ttl", "Turtle", TTL_FMT, TTL_MT)]),
    ("thesaurus", "Minimal Brick thesaurus (SKOS)",
     "SKOS thesaurus of colours with hex approximations, part designs and categories, features, units and identifier systems. Every concept names its sources and a verification status.",
     ["thesaurus", "SKOS", "colours", "parts"], "thesaurus.html",
     [("thesaurus.ttl", "Turtle", TTL_FMT, TTL_MT), ("colours.csv", "CSV", CSV_FMT, CSV_MT), ("thesaurus.json", "JSON", JSON_FMT, JSON_MT)]),
    ("shapes", "SHACL shapes for the Minimal Brick Ontology and its DCAT-AP catalogue",
     "SHACL shapes for the thesaurus, the ontology classes and build descriptions, plus a hand-written subset of the DCAT-AP 3.0 requirements.",
     ["SHACL", "validation"], "index.html",
     [("mbo-shapes.ttl", "Turtle", TTL_FMT, TTL_MT), ("dcat-ap-subset-shapes.ttl", "Turtle", TTL_FMT, TTL_MT)]),
    ("example", "Worked example: stepped pyramid and minifigure",
     "A build description with layers, pieces, elements and a CRMdig reconstruction derivation. Layer sizes follow the author's reconstruction; the brick tiling is illustrative.",
     ["example", "build", "reconstruction"], "index.html", [("example-pyramid.ttl", "Turtle", TTL_FMT, TTL_MT)]),
]


def build() -> Graph:
    g = Graph()
    cat = URIRef("https://w3id.org/mbo/catalogue")
    agent = URIRef("https://w3id.org/mbo/agent/research-squirrel-engineers")
    g.add((agent, RDF.type, FOAF.Agent))
    g.add((agent, RDF.type, FOAF.Organization))
    g.add((agent, FOAF.name, Literal("Research Squirrel Engineers")))
    g.add((agent, FOAF.homepage, URIRef("https://github.com/Research-Squirrel-Engineers")))
    g.add((cat, RDF.type, DCAT.Catalog))
    g.add((cat, DCTERMS.title, Literal("Minimal Brick Ontology catalogue", lang="en")))
    g.add((cat, DCTERMS.description, Literal("Catalogue of the datasets of the Minimal Brick Ontology: ontology, thesaurus, shapes and a worked example.", lang="en")))
    g.add((cat, DCTERMS.publisher, agent))
    g.add((cat, DCTERMS.language, ENG))
    g.add((cat, DCTERMS.license, CC_BY))
    g.add((cat, DCTERMS.issued, Literal(U.RELEASE, datatype=XSD.date)))
    g.add((cat, DCTERMS.modified, Literal(U.RELEASE, datatype=XSD.date)))
    g.add((cat, FOAF.homepage, URIRef(U.PAGES)))
    for slug, title, desc, kws, landing, dists in DATASETS:
        ds = URIRef(f"https://w3id.org/mbo/dataset/{slug}")
        g.add((cat, DCAT.dataset, ds))
        g.add((ds, RDF.type, DCAT.Dataset))
        g.add((ds, DCTERMS.title, Literal(title, lang="en")))
        g.add((ds, DCTERMS.description, Literal(desc, lang="en")))
        g.add((ds, DCTERMS.publisher, agent))
        g.add((ds, DCTERMS.language, ENG))
        g.add((ds, DCTERMS.license, CC_BY))
        g.add((ds, DCTERMS.accessRights, PUBLIC))
        g.add((ds, DCTERMS.issued, Literal(U.RELEASE, datatype=XSD.date)))
        g.add((ds, DCTERMS.modified, Literal(U.RELEASE, datatype=XSD.date)))
        g.add((ds, DCAT.landingPage, URIRef(U.PAGES + landing)))
        for k in kws:
            g.add((ds, DCAT.keyword, Literal(k, lang="en")))
        for fname, label, fmt, mt in dists:
            d = URIRef(f"https://w3id.org/mbo/distribution/{fname.replace('.', '-')}")
            g.add((ds, DCAT.distribution, d))
            g.add((d, RDF.type, DCAT.Distribution))
            g.add((d, DCTERMS.title, Literal(f"{fname} ({label})", lang="en")))
            g.add((d, DCAT.accessURL, URIRef(U.PAGES + fname)))
            g.add((d, DCAT.downloadURL, URIRef(U.PAGES + fname)))
            g.add((d, DCTERMS.format, fmt))
            g.add((d, DCAT.mediaType, mt))
            g.add((d, DCTERMS.license, CC_BY))
    return g


def main() -> int:
    U.ensure_dirs()
    g = build()
    n = U.write_turtle(g, U.DIST / "catalogue.ttl")
    print(f"catalogue: {n} triples, {len(DATASETS)} datasets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
