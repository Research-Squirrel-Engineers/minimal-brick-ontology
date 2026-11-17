# Minimal Brick Ontology (MBO)

A small OWL ontology and SKOS thesaurus for describing interlocking building bricks, plates,
tiles and minifigure parts, and the models built from them.

* **Ontology** aligned to CIDOC CRM (E22, E55, E58, E99), CRMba (B1, B2) and CRMdig (D1, D3)
* **SKOS thesaurus** of colours (with hex approximations), part designs and categories,
  features, units and identifier systems; every concept names its sources and a verification status
* **SHACL shapes** for the thesaurus, the ontology classes and build descriptions
* **DCAT-AP 3.0 catalogue** (validated against a hand-written subset of the profile)
* **Documentation site** with a click-through hierarchical thesaurus (GitHub Pages)
* **Build exporter** that turns a JSON build spec into RDF (layers, pieces, positions, CRMdig derivation)

> Independent community vocabulary. Not affiliated with, authorised or endorsed by the LEGO
> Group. LEGO is a trademark of the LEGO Group. The LEGO Group publishes no open technical
> specification that we could retrieve; dimensions are nominal values from community sources
> and are marked as such.

Namespace: `https://w3id.org/mbo/` (redirects prepared in `w3id/`, pending registration).
Documentation: https://research-squirrel-engineers.github.io/minimal-brick-ontology/

## Quick start (Windows cmd, one line)

    python -m venv .venv && call .venv\Scripts\activate && pip install -r requirements.txt && python main.py

All offline steps run from the seed data in `data/seed/`. To add every colour and part of the
Rebrickable catalogue (the only network step), then rebuild:

    python main.py fetch && python main.py

Look at the site locally:

    python -m http.server --directory docs 8000

then open http://localhost:8000/. Other commands: `python main.py --list`, `--only docs`,
`--from validate`, `--dry-run`, `--strict`.

## Describe a build

    python py/mbo_build.py data/examples/pyramid_spec.json my-build.ttl

A spec lists layers of pieces (part number, colour slug, stud position, rotation). The exporter
rejects unknown parts or colours and overlapping pieces. See the docstring of `py/mbo_build.py`.
Grid units are studs (X, Y) and plate heights (Z); a brick layer is three plates.

## Layout

    ontology/mbo.ttl            hand-written OWL source
    shapes/                     SHACL: MBO shapes, DCAT-AP subset
    data/seed/                  sources, colours, parts, vocabulary (CSV)
    data/raw/rebrickable/       Rebrickable downloads, unchanged (after `main.py fetch`)
    py/                         one module per step; mbo_build.py is the build exporter
    dist/                       generated: thesaurus, example, catalogue, reports
    docs/                       generated: GitHub Pages site and downloads
    w3id/                       redirect rules for the w3id.org pull request
    PRIMER.md                   German work plan (decisions, steps, open points)

## Trust and provenance

Every concept has `dct:source` links and `mbo:verification`: `sourced` (a retrieved source states
it), `seed` (author-supplied, not yet confirmed), `rebrickable` (from the Rebrickable download),
`derived` (computed). Seed hex values are approximations until the Rebrickable colours are loaded.
The CIDOC CRM alignment axioms are hand-written and not machine-checked against the CRM RDFS files.
The DCAT-AP check is a subset; run the official DCAT-AP shapes before submitting to a portal.

## Licence

Vocabulary, data and documentation: CC BY 4.0 (`LICENSE-DATA.md`). Code: MIT (`LICENSE`).
