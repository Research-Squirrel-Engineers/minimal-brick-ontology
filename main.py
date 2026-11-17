#!/usr/bin/env python3
"""Single entry point of minimal-brick-ontology.

    python main.py                 all offline steps, in order
    python main.py fetch           download the Rebrickable CSVs (the only network step)
    python main.py --list          print steps and exit
    python main.py --only docs     one step
    python main.py --from validate this step and everything after
    python main.py --skip docs     everything but this step
    python main.py --dry-run       print the plan, run nothing
    python main.py --strict        warnings become errors (what CI runs)

Steps run as subprocesses of py/step_<name>.py, so each stays runnable standalone
and --list / --dry-run import nothing heavy. Step output is passed through line
by line and written to dist/pipeline_report.txt (no clock in the report).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# name, script, in default run, description
STEPS = [
    ("fetch", "step_fetch.py", False, "download Rebrickable colours, part categories and parts (network)"),
    ("thesaurus", "step_thesaurus.py", True, "SKOS thesaurus from seed data (+ Rebrickable files if present)"),
    ("example", "step_example.py", True, "worked example build (pyramid + minifigure) as RDF"),
    ("catalogue", "step_catalogue.py", True, "DCAT-AP catalogue"),
    ("validate", "step_validate.py", True, "parse, vocabulary closure, SHACL (MBO + DCAT-AP subset)"),
    ("diagram", "step_diagram.py", True, "ontology overview figure (SVG, Mermaid)"),
    ("docs", "step_docs.py", True, "GitHub Pages site in docs/"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", nargs="?", choices=[s[0] for s in STEPS if not s[2]], help="run a step that is not part of the default run")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--from", dest="start")
    ap.add_argument("--skip")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    names = [s[0] for s in STEPS]
    if a.list:
        for n, script, default, desc in STEPS:
            print(f"{n:<10} {'default' if default else 'verb   '}  {desc}")
        return 0
    if a.verb:
        plan = [a.verb]
    else:
        plan = [s[0] for s in STEPS if s[2]]
        if a.only:
            plan = [a.only]
        if a.start:
            plan = [n for n in names if names.index(n) >= names.index(a.start) and (n in plan or n == a.start)]
        if a.skip:
            plan = [n for n in plan if n != a.skip]
    for n in plan:
        if n not in names:
            print(f"unknown step {n!r}; try --list")
            return 2
    if a.dry_run:
        for n in plan:
            print("would run", n)
        return 0

    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0")
    if a.strict:
        env["MBO_STRICT"] = "1"
    (ROOT / "dist").mkdir(exist_ok=True)
    report: list[str] = []
    times: list[tuple[str, float]] = []
    rc_total = 0
    for n in plan:
        script = next(s[1] for s in STEPS if s[0] == n)
        print(f"== {n}")
        report.append(f"== {n}")
        t0 = time.perf_counter()
        proc = subprocess.Popen([sys.executable, "-I", str(ROOT / "py" / script)], cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        for line in proc.stdout:
            line = line.rstrip("\n")
            print("  " + line)
            report.append("  " + line)
        rc = proc.wait()
        times.append((n, time.perf_counter() - t0))
        if rc != 0:
            print(f"step {n} failed with exit code {rc}")
            rc_total = rc
            break
    if n != "fetch" and not a.verb:
        (ROOT / "dist" / "pipeline_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    total = sum(t for _, t in times) or 1
    print("\nstep        seconds   share")
    for n, t in times:
        print(f"{n:<10} {t:8.2f} {100 * t / total:6.1f}%")
    return rc_total


if __name__ == "__main__":
    sys.exit(main())
