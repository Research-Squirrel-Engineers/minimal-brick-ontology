"""Generate the GitHub Pages site in docs/ (static HTML, no Jekyll).

Pages: index.html, ontology.html, thesaurus.html (click-through hierarchical
thesaurus). Copies the Turtle/CSV/JSON products next to the pages so that the
catalogue's access URLs resolve. Run standalone: python py/step_docs.py
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

import mbo_utils as U

TPL = U.ROOT / "py" / "templates"
E = html.escape
INLINE_LIMIT = 1_500_000
COPIES = [
    (U.ONTOLOGY / "mbo.ttl", "ontology.ttl"), (U.DIST / "thesaurus.ttl", "thesaurus.ttl"), (U.DIST / "colours.csv", "colours.csv"),
    (U.DIST / "thesaurus.json", "thesaurus.json"), (U.DIST / "example-pyramid.ttl", "example-pyramid.ttl"),
    (U.DIST / "catalogue.ttl", "catalogue.ttl"), (U.SHAPES / "mbo-shapes.ttl", "mbo-shapes.ttl"),
    (U.SHAPES / "dcat-ap-subset-shapes.ttl", "dcat-ap-subset-shapes.ttl"),
]
PREFIX_SHORT = [(U.NS["mbo"], "mbo:"), (U.NS["crm"], "crm:"), (U.NS["crmba"], "crmba:"), (U.NS["crmdig"], "crmdig:"),
                (U.NS["xsd"], "xsd:"), (U.NS["skos"], "skos:")]


def short(uri) -> str:
    s = str(uri)
    for ns, p in PREFIX_SHORT:
        if s.startswith(ns):
            return p + s[len(ns):].replace("_", " ", 1) if p.startswith("crm") else p + s[len(ns):]
    return s


def nav(active: str) -> str:
    docs = [("index.html", "Overview"), ("ontology.html", "Ontology"), ("thesaurus.html", "Thesaurus")]
    dl = [("ontology.ttl", "ontology.ttl"), ("thesaurus.ttl", "thesaurus.ttl"), ("mbo-shapes.ttl", "shapes"), ("catalogue.ttl", "DCAT-AP catalogue")]
    def row(label, items):
        a = "".join(f'<a href="{h}"{" class=on" if h == active else ""}>{E(t)}</a>' for h, t in items)
        cls = "docs" if label == "Documentation" else "dl"
        return f'<div class="row {cls}"><span class="lab">{label}</span>{a}</div>'
    return '<nav class="card">' + row("Documentation", docs) + row("Downloads", dl) + "</nav>"


def page(name: str, title: str, body: str, head: str = "", tail: str = "") -> None:
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><link rel="stylesheet" href="assets/site.css">{head}</head>
<body><header class="site"><div class="title">Minimal Brick Ontology (MBO) {U.VERSION}</div>{nav(name)}</header>
<main>{body}</main>{tail}</body></html>"""
    U.write_text(U.DOCS / name, doc)


def verification_counts(js: dict) -> dict:
    out: dict[str, dict[str, int]] = {}
    for c in js["concepts"].values():
        out.setdefault(c["scheme"], {}).setdefault(c["verification"] or "derived", 0)
        out[c["scheme"]][c["verification"] or "derived"] += 1
    return out


def index_page(js: dict) -> None:
    counts = verification_counts(js)
    labels = {s["id"]: s["label"] for s in js["schemes"]}
    stat_rows = "".join(
        f"<tr><td>{E(labels[s])}</td>" + "".join(f"<td>{counts[s].get(v, 0)}</td>" for v in ("sourced", "seed", "rebrickable")) + "</tr>"
        for s in labels)
    ns_rows = "".join(f"<tr><td><code>{p}</code></td><td><code>{E(i)}</code></td><td>{E(d)}</td></tr>" for p, i, d in [
        ("mbo:", U.NS["mbo"], "Ontology terms (classes and properties)"),
        ("mbot:", U.NS["mbot"], "Thesaurus: colour/, part/, feature/, unit/, identifier-system/"),
        ("mbox:", U.NS["mbox"], "Worked example"),
        ("mbos:", U.NS["mbos"], "Source records"),
        ("catalogue", "https://w3id.org/mbo/catalogue", "DCAT-AP catalogue"),
    ])
    dl_rows = ""
    for _src, name in COPIES:
        size = (U.DOCS / name).stat().st_size
        dl_rows += f'<tr><td><a href="{name}">{name}</a></td><td>{size:,} bytes</td></tr>'
    src_rows = "".join(
        f'<tr><td><a href="{E(r["url"])}">{E(r["title"])}</a></td><td>{E(r["kind"])}</td><td>{E(r["note"])}</td></tr>'
        for r in sorted(U.read_csv(U.SEED / "sources.csv"), key=lambda r: (r["kind"], r["id"])))
    body = f"""
<h1>Minimal Brick Ontology</h1>
<article class="card">
<p>A small OWL ontology and SKOS thesaurus for describing interlocking building bricks, plates, tiles and minifigure parts, and the models built from them.
The ontology is aligned to CIDOC CRM (E22, E55, E58, E99), CRMba (B1, B2) and CRMdig (D1, D3); the catalogue follows DCAT-AP 3.0; the thesaurus and the build
descriptions are validated with SHACL.</p>
<blockquote>Independent community vocabulary. It is not affiliated with, authorised or endorsed by the LEGO Group. LEGO is a trademark of the LEGO Group.
The LEGO Group publishes no open technical specification that we could retrieve, so every dimension is a nominal value from community sources, and every
concept names the sources behind it.</blockquote>
</article>
<section class="card"><h2>What is verified</h2>
<p>Each concept carries a verification status: <span class="badge b-sourced">sourced</span> a retrieved source states it,
<span class="badge b-seed">seed</span> author-supplied and not yet confirmed, <span class="badge b-rebrickable">rebrickable</span> taken from the Rebrickable download.
Hex values of the seed colours are approximations that are replaced when the Rebrickable colours file is processed
(<code>python main.py fetch</code>).</p>
<table><tr><th>Scheme</th><th>sourced</th><th>seed</th><th>rebrickable</th></tr>{stat_rows}</table>
</section>
<section class="card"><h2>Explore</h2><div class="grid">
<div><h3><a href="thesaurus.html">Thesaurus</a></h3><p class="muted">Click through colours, part categories, parts, features, units and identifier systems, with hex swatches and sources.</p></div>
<div><h3><a href="ontology.html">Ontology</a></h3><p class="muted">Classes, properties and the CIDOC CRM alignment, with an overview figure.</p></div>
</div></section>
<section class="card"><h2>Namespaces</h2>
<table><tr><th>Prefix</th><th>IRI</th><th>Use</th></tr>{ns_rows}</table>
<p class="muted">The w3id.org/mbo/ redirects are prepared in the repository (<code>w3id/mbo/</code>) and take effect once the pull request to perma-id/w3id.org is merged.</p>
</section>
<section class="card"><h2>Use it in a reconstruction workflow</h2>
<p>A build is described by a small JSON spec (layers of pieces with part number, colour, stud position and rotation). The exporter checks part numbers, colours and overlaps and writes Turtle:</p>
<pre>python py/mbo_build.py data/examples/pyramid_spec.json my-build.ttl</pre>
<p>Parts and colours are referred to by their thesaurus slugs, for example part <code>3001</code> (Brick 2 x 4) in colour <code>white</code>.
Grid units are studs (X, Y) and plate heights (Z); one brick layer is three plates high.</p></section>
<section class="card"><h2>Downloads</h2><table><tr><th>File</th><th>Size</th></tr>{dl_rows}</table></section>
<section class="card"><h2>Sources</h2><table><tr><th>Source</th><th>Kind</th><th>What was taken from it</th></tr>{src_rows}</table></section>
<section class="card"><h2>Licence</h2><p>Ontology, thesaurus and documentation: CC BY 4.0. Code: MIT. Rebrickable data is not redistributed in the repository; it is downloaded by the user.</p></section>
"""
    page("index.html", "Minimal Brick Ontology", body)


def ontology_page() -> None:
    g = Graph()
    g.parse(U.ONTOLOGY / "mbo.ttl", format="turtle")
    mbo = U.NS["mbo"]

    def lab(s):
        for o in g.objects(s, RDFS.label):
            if getattr(o, "language", None) == "en":
                return str(o)
        return short(s)

    cls_rows, prop_rows = [], []
    for s in sorted(g.subjects(RDF.type, OWL.Class), key=str):
        if not str(s).startswith(mbo):
            continue
        sup = ", ".join(sorted(short(o) for o in g.objects(s, RDFS.subClassOf)))
        de = "".join(str(o) for o in g.objects(s, RDFS.label) if getattr(o, "language", "") == "de")
        d = "".join(str(o) for o in g.objects(s, SKOS.definition))
        cls_rows.append(f"<tr><td><code>{short(s)}</code></td><td>{E(lab(s))}<br><span class='muted'>{E(de)}</span></td><td>{E(sup)}</td><td>{E(d)}</td></tr>")
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for s in sorted(g.subjects(RDF.type, kind), key=str):
            if not str(s).startswith(mbo):
                continue
            dom = ", ".join(short(o) for o in g.objects(s, RDFS.domain)) or "any"
            rng = ", ".join(short(o) for o in g.objects(s, RDFS.range))
            sup = ", ".join(short(o) for o in g.objects(s, RDFS.subPropertyOf))
            inv = ", ".join(short(o) for o in g.objects(s, OWL.inverseOf))
            c = "".join(str(o) for o in g.objects(s, RDFS.comment))
            prop_rows.append(f"<tr><td><code>{short(s)}</code></td><td>{'object' if kind == OWL.ObjectProperty else 'data'}</td><td>{E(dom)}</td><td>{E(rng)}</td>"
                             f"<td>{E(sup)}{' inverse of ' + E(inv) if inv else ''}</td><td>{E(c)}</td></tr>")
    svg = (U.DOCS / "assets" / "ontology-overview.svg").read_text(encoding="utf-8")
    body = f"""
<h1>Ontology</h1>
<section class="card figure">{svg}
<div class="figcap"><span class="n">Figure 1</span><span>Core classes and properties. Orange: MBO classes; purple: classes whose instances are SKOS concepts; white: external CRM class. The second line names the CIDOC CRM or extension class each MBO class specialises.</span></div>
<p class="muted"><a href="assets/ontology-overview.svg">SVG</a> · <a href="assets/ontology-overview.mmd">Mermaid source</a> · <a href="ontology.ttl">ontology.ttl</a></p></section>
<section class="card"><h2>Alignment to CIDOC CRM</h2>
<ul><li><strong>Types:</strong> element designs and elements are <code>crm:E99 Product Type</code>; colours, categories, features and identifier systems are <code>crm:E55 Type</code>; units are <code>crm:E58 Measurement Unit</code>.
An element is a narrower type of its design (<code>P127</code>) and carries its colour through <code>P2 has type</code>.</li>
<li><strong>Things:</strong> a piece is a <code>crm:E22 Human-Made Object</code> typed by an element; assemblies and minifigures are E22 composed of pieces (<code>P46</code>).</li>
<li><strong>CRMba:</strong> a build is a <code>B1 Built Work</code>, a layer a <code>B2 Morphological Building Section</code> (<code>BP1 is section of</code>).</li>
<li><strong>CRMdig:</strong> a build model is a <code>D1 Digital Object</code>; a reconstruction is a <code>D3 Formal Derivation</code> using <code>L21</code> and <code>L22</code>.</li></ul>
<blockquote>The alignment axioms were written by hand and have not been machine-checked against the published CRM RDFS files.</blockquote></section>
<section class="card"><h2>Classes</h2><table><tr><th>Class</th><th>Label</th><th>Specialises</th><th>Definition</th></tr>{''.join(cls_rows)}</table></section>
<section class="card"><h2>Properties</h2><table><tr><th>Property</th><th>Kind</th><th>Domain</th><th>Range</th><th>Aligned to</th><th>Note</th></tr>{''.join(prop_rows)}</table></section>
"""
    page("ontology.html", "MBO ontology", body)


def thesaurus_page(js: dict) -> None:
    raw = (U.DIST / "thesaurus.json").read_text(encoding="utf-8")
    if len(raw.encode("utf-8")) <= INLINE_LIMIT:
        safe = raw.replace("</", "<\\/")
        data_tag = f'<script>window.MBO_DATA={safe};</script>'
        loader = '<script src="assets/thesaurus.js"></script>'
    else:
        data_tag = ""
        loader = ('<script>fetch("thesaurus.json").then(function(r){return r.json()}).then(function(d){window.MBO_DATA=d;'
                  'var s=document.createElement("script");s.src="assets/thesaurus.js";document.body.appendChild(s)})'
                  '.catch(function(){document.getElementById("tree").textContent="Could not load thesaurus.json. Serve this folder over HTTP: python -m http.server --directory docs"})</script>')
    body = """
<h1>Thesaurus</h1>
<section class="card"><p class="muted" style="margin:0">Click a node to open it; click a label for details, identifiers and sources. Deep links work: <code>thesaurus.html#colour/white</code>.</p>
<div class="tabs" id="tabs"></div>
<div class="tools"><input id="q" type="search" placeholder="Search label, number or #hex">
<select id="ver"><option value="">any status</option><option>sourced</option><option>seed</option><option>rebrickable</option></select>
<button id="expand">Expand all</button><button id="collapse">Collapse all</button></div>
<div class="app"><div class="treebox" id="tree"></div><div class="card detail" id="detail"><p class="muted">Select a concept.</p></div></div></section>
"""
    page("thesaurus.html", "MBO thesaurus", body, tail=data_tag + loader)


def main() -> int:
    U.ensure_dirs()
    for src, name in COPIES:
        shutil.copyfile(src, U.DOCS / name)
    shutil.copyfile(TPL / "site.css", U.DOCS / "assets" / "site.css")
    shutil.copyfile(TPL / "thesaurus.js", U.DOCS / "assets" / "thesaurus.js")
    U.write_text(U.DOCS / ".nojekyll", "")
    js = json.loads((U.DIST / "thesaurus.json").read_text(encoding="utf-8"))
    index_page(js)
    ontology_page()
    thesaurus_page(js)
    print("docs: index.html, ontology.html, thesaurus.html + downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
