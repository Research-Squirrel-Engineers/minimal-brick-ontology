"""Build the worked example: an illustrative stepped pyramid plus a minifigure.

Layer sizes (in studs) come from the author's reconstruction chat
(source id: user-chat-pyramid). The placement of individual bricks is a
deterministic greedy tiling (2x4 along X, then 2x2), NOT the measured layout.
Outputs: data/examples/pyramid_spec.json (generated), dist/example-pyramid.ttl
Run standalone: python py/step_example.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mbo_build as B
import mbo_utils as U

LAYER_SIZES = [(14, 18), (12, 16), (10, 14), (8, 12), (6, 10), (4, 8), (2, 6), (2, 4), (2, 2)]


def tile_layer(w: int, d: int, ox: int, oy: int) -> list[dict]:
    pieces = []
    for y in range(0, d, 2):
        x = 0
        while x < w:
            if w - x >= 4:
                pieces.append({"part": "3001", "colour": "White", "x": ox + x, "y": oy + y, "rot": 0})
                x += 4
            else:
                pieces.append({"part": "3003", "colour": "White", "x": ox + x, "y": oy + y, "rot": 0})
                x += 2
    return pieces


def make_spec() -> dict:
    mw = max(w for w, _ in LAYER_SIZES)
    md = max(d for _, d in LAYER_SIZES)
    layers = []
    for i, (w, d) in enumerate(LAYER_SIZES):
        layers.append({"index": i, "pieces": tile_layer(w, d, (mw - w) // 2, (md - d) // 2)})
    w, d = LAYER_SIZES[-1]
    cx, cy = (mw - w) // 2, (md - d) // 2
    for k in range(5):
        layers.append({"index": len(LAYER_SIZES) + k, "pieces": [{"part": "3005", "colour": "White", "x": cx, "y": cy, "rot": 0}]})
    return {
        "id": "pyramid-white",
        "label": "Stepped white pyramid with column",
        "description": "Illustrative example. Layer sizes follow the author's reconstruction; the tiling of single bricks is a deterministic greedy layout, not the measured one.",
        "source": "user-chat-pyramid",
        "scale": "0.6667",
        "scan": {"label": "KIRI Engine structure-from-motion scan (not included)"},
        "layers": layers,
        "assemblies": [{"id": "minifigure-1", "type": "Minifigure", "label": "Illustrative minifigure", "pieces": [
            {"part": "3626", "colour": "Yellow"}, {"part": "973", "colour": "Blue"}, {"part": "3815", "colour": "Black"},
            {"part": "3816", "colour": "Black"}, {"part": "3817", "colour": "Black"},
            {"part": "3818", "colour": "Blue"}, {"part": "3819", "colour": "Blue"}, {"part": "3820", "colour": "Yellow"}]}],
    }


def main() -> int:
    U.ensure_dirs()
    spec = make_spec()
    U.write_json(U.DATA / "examples" / "pyramid_spec.json", spec)
    g = B.export_build(spec)
    n = U.write_turtle(g, U.DIST / "example-pyramid.ttl")
    pieces = sum(len(l["pieces"]) for l in spec["layers"])
    print(f"example: {len(spec['layers'])} layers, {pieces} pieces, {n} triples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
