"""Draw the ontology overview as a deterministic SVG plus a Mermaid source.

Figure rules (PRIMER.md A3): English only, no header or footer text, property
labels as amber chips (#fbbf24) centred on the middle of each arrow. Colours:
class #9a3412, term #4c1d95, external OWL/CRM class white.
Outputs: docs/assets/ontology-overview.svg, docs/assets/ontology-overview.mmd
Run standalone: python py/step_diagram.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mbo_utils as U

BW, BH, GX, GY, X0, Y0 = 300, 66, 590, 190, 40, 40
FONT = "Fira Sans, Arial, sans-serif"
STYLE = {  # kind -> (fill, stroke, text)
    "class": ("#9a3412", "#000000", "#ffffff"),
    "term": ("#4c1d95", "#000000", "#ffffff"),
    "owl": ("#ffffff", "#000000", "#000000"),
}
# id: (col, row, kind, title, subtitle)
NODES = {
    "cat": (0, 0, "term", "Part category", "SKOS concepts, crm:E55 Type"),
    "design": (1, 0, "class", "Element design", "crm:E99 Product Type"),
    "feat": (2, 0, "term", "Feature", "SKOS concepts, crm:E55 Type"),
    "elem": (1, 1, "class", "Element", "crm:E99 Product Type"),
    "col": (2, 1, "term", "Colour", "SKOS concepts, crm:E55 Type"),
    "asm": (0, 2, "class", "Assembly", "crm:E22 Human-Made Object"),
    "piece": (1, 2, "class", "Piece", "crm:E22 Human-Made Object"),
    "layer": (2, 2, "class", "Layer", "crmba:B2 Morphological Building Section"),
    "mini": (0, 3, "class", "Minifigure", "subclass of Assembly"),
    "model": (1, 3, "class", "Build model", "crmdig:D1 Digital Object"),
    "build": (2, 3, "class", "Build", "crmba:B1 Built Work"),
    "proc": (1, 4, "class", "Reconstruction process", "crmdig:D3 Formal Derivation"),
    "scan": (2, 4, "owl", "crmdig:D1 Digital Object", "the scan"),
}
EDGES = [  # source, target, label
    ("design", "cat", "skos:broader"),
    ("design", "feat", "hasFeature"),
    ("elem", "design", "hasDesign"),
    ("elem", "col", "hasColour"),
    ("piece", "elem", "instanceOfElement"),
    ("piece", "layer", "inLayer"),
    ("asm", "piece", "hasPiece"),
    ("layer", "build", "isLayerOf"),
    ("mini", "asm", "subClassOf"),
    ("model", "build", "describesBuild"),
    ("proc", "model", "L22 created derivative"),
    ("proc", "scan", "L21 derivation source"),
]


def box(n):
    c, r, *_ = NODES[n]
    return X0 + c * GX, Y0 + r * GY


def anchor(a, b):
    ax, ay = box(a)
    bx, by = box(b)
    if ay == by:  # same row
        if bx > ax:
            return (ax + BW, ay + BH / 2), (bx, by + BH / 2)
        return (ax, ay + BH / 2), (bx + BW, by + BH / 2)
    if by > ay:
        return (ax + BW / 2, ay + BH), (bx + BW / 2, by)
    return (ax + BW / 2, ay), (bx + BW / 2, by + BH)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg() -> str:
    W = X0 * 2 + 2 * GX + BW
    H = Y0 * 2 + 4 * GY + BH
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#000000"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for a, b, label in EDGES:
        (x1, y1), (x2, y2) = anchor(a, b)
        out.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="#000000" stroke-width="2" marker-end="url(#ah)"/>')
    for a, b, label in EDGES:
        (x1, y1), (x2, y2) = anchor(a, b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        w = len(label) * 8.2 + 22
        out.append(f'<rect x="{mx - w / 2:g}" y="{my - 14:g}" width="{w:g}" height="28" rx="14" fill="#fbbf24" stroke="#000000" stroke-width="1"/>')
        out.append(f'<text x="{mx:g}" y="{my + 5:g}" text-anchor="middle" font-size="15" fill="#000000">{esc(label)}</text>')
    for n, (c, r, kind, title, sub) in NODES.items():
        x, y = box(n)
        fill, stroke, tc = STYLE[kind]
        out.append(f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        out.append(f'<text x="{x + BW / 2}" y="{y + 28}" text-anchor="middle" font-size="19" font-weight="500" fill="{tc}">{esc(title)}</text>')
        out.append(f'<text x="{x + BW / 2}" y="{y + 50}" text-anchor="middle" font-size="13" fill="{tc}">{esc(sub)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def build_mermaid() -> str:
    ids = {n: n.upper() for n in NODES}
    lines = ["flowchart TB"]
    for n, (_c, _r, kind, title, sub) in NODES.items():
        lines.append(f'    {ids[n]}(["{title}<br/><small>{sub}</small>"])')
    for a, b, label in EDGES:
        lines.append(f'    {ids[a]} -->|"{label}"| {ids[b]}')
    lines += [
        "    classDef Class fill:#9a3412,stroke:#000000,color:#ffffff",
        "    classDef Term fill:#4c1d95,stroke:#000000,color:#ffffff",
        "    classDef OWL fill:#ffffff,stroke:#000000,color:#000000",
        "    classDef PropMeta fill:#fbbf24,stroke:#000000,color:#000000",
    ]
    for kind, cls in (("class", "Class"), ("term", "Term"), ("owl", "OWL")):
        members = [ids[n] for n, v in NODES.items() if v[2] == kind]
        lines.append(f"    class {','.join(members)} {cls}")
    return "\n".join(lines)


def main() -> int:
    U.ensure_dirs()
    U.write_text(U.DOCS / "assets" / "ontology-overview.svg", build_svg())
    U.write_text(U.DOCS / "assets" / "ontology-overview.mmd", build_mermaid())
    print("diagram: docs/assets/ontology-overview.svg, .mmd")
    return 0


if __name__ == "__main__":
    sys.exit(main())
