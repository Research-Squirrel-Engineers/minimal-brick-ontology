# PRIMER — minimal-brick-ontology

Arbeitsplan für das Repo `Research-Squirrel-Engineers/minimal-brick-ontology`. Wird zu Beginn
jedes Chats hochgeladen und am Ende zurückgeschrieben. Teil A gilt immer, Teil B ist die
Schrittübersicht, Teil C beschreibt die Schritte, Teil D sammelt Offenes.

# Teil A — Immer gültig

## A1 Ausgangslage

Ziel: eine Minimal-Ontologie (OWL) plus SKOS-Thesaurus für Steine, Platten (und Fliesen, Grundplatten)
sowie Minifiguren, mit Farben samt Hex, damit LEGO-Bauten beschrieben werden können. Anlass ist
der Rekonstruktions-Chat „Lego-Stein 3D-Modell rekonstruieren“ (KIRI-Scans, Stufenpyramiden, 2/3-Szenenmaßstab).

| Was | Stand |
|---|---|
| Repo | neu, dieses Gerüst (Stand 2026-11-18) |
| Ontologie | `ontology/mbo.ttl`, 49 Terme, handgeschrieben |
| Thesaurus | Seed: 25 Farben (+ 4 Farbgruppen), 47 Teile (+ 12 Kategorien), 3 Merkmale, 8 Einheiten, 5 Nummernsysteme |
| Beispiel | Stufenpyramide (14 Ebenen, 118 Teile) + Minifigur |

**Befunde (geprüft 2026-11-18):**

- Eine offene, offizielle Maßspezifikation der LEGO Group wurde nicht gefunden. Alle Maße stammen aus
  Community-Quellen (LUGNET-FAQ, LDraw, Brickfact u. a.). Gemessene Werte weichen leicht von den
  Nennwerten ab: Steinhöhe 9,582 mm statt 9,6 mm, Plattenhöhe 3,194 mm statt 3,2 mm, Noppenabstand
  7,985 mm statt 8 mm. Die Nennwerte stehen im Thesaurus, die Messwerte als Notiz.
- Die LEGO-Farbpalette wurde 2010 von der LEGO Design Lab veröffentlicht (Namen und Nummern, ohne
  RGB/CMYK). Das PDF selbst wurde nicht gelesen, nur die Meldung darüber. **Offen: PDF einpflegen (S6).**
- Farbquellen mit Hex waren aus dem Sandbox-Chat nicht erreichbar: `cdn.rebrickable.com` per Proxy
  abgelehnt (403), `rebrickable.com/colors/` Client-Fehler, `peeron.com` robots-gesperrt,
  `ryanhowerter.net` Client-Fehler, Brickimedia hinter Anubis-Schranke. Darum gibt es `main.py fetch`.
- Die Seed-Hexwerte (Status `seed`) stammen aus dem Gedächtnis des Modells und sind **nicht** verifiziert.
  Transparente Farben haben im Seed bewusst keinen Hex.
- Seed-Teilenummern (außer 3069b und 4073/6141) sind ebenfalls nicht durch eine abgerufene Quelle
  belegt; `main.py fetch` bestätigt sie gegen `parts.csv`.
- Minifigurenteile (geprüft 2026-11-18 gegen `parts.csv`): Rebrickable-Kategorien heißen `Minifig Heads`, `Minifig Upper Body`, `Minifig Lower Body`, `Minifig Headwear` (nicht Torsos/Arms/Hands); Oberkörper und Unterkörper enthalten Torso, Arme, Hände bzw. Hüfte und Beine gemischt, daher entscheidet der Teilename. 3815, 3816–3820 stehen unverändert in `parts.csv`. Der Kopf heißt dort nur 3626a/b/c (plain), die Torsonummer 973 gibt es nur mit Suffix und als Druck; 973 bleibt `seed`. Muster-Varianten (`pat`, `pats`, `px`, `ps`, `p<Ziffer>`) zählen wie `pr`/`pb` als Drucke und sind nicht im Umfang.
- Das Wort „Brick“ kollidiert mit dem Brick Schema (Gebäudetechnik). Daher der Name `minimal-brick-ontology`/MBO.

## A2 Zielbild

```
data/seed/*.csv ─┐
data/raw/rebrickable/*.csv ─┤→ step_thesaurus → dist/thesaurus.ttl, colours.csv, thesaurus.json
ontology/mbo.ttl ─┤                              │
shapes/*.ttl ─────┤→ step_example → dist/example-pyramid.ttl
                  │  step_catalogue → dist/catalogue.ttl (DCAT-AP)
                  │  step_validate → SHACL (MBO + DCAT-AP-Subset)   ← Gate vor docs
                  └→ step_diagram, step_docs → docs/ (GitHub Pages)
build-spec.json ──→ py/mbo_build.py → RDF eines Bauwerks (im Rekonstruktions-Chat)
```

Eigenschaften, die das Ergebnis haben muss (prüfbar):

1. `python main.py` läuft offline, `RESULT OK` in `dist/validation_report.txt`.
2. Zwei Läufe hintereinander: `git status` sauber (keine Uhr im Output).
3. Jedes Konzept hat mindestens eine `dct:source` und genau einen `mbo:verification`-Wert.
4. Jede Farbe hat entweder `hexColour` (6 Ziffern, groß) oder keinen Hex; nie einen erfundenen.
5. Der Exporter lehnt unbekannte Teile/Farben und Überlappungen ab.

## A3 Querschnittsregeln

- Rohdaten in `data/raw/rebrickable/` unverändert, Produkte in `dist/` und `docs/`. Beides wird versioniert, damit ein Clone identisch baut.
- Keine Uhr im Output: Datum kommt aus `RELEASE` in `py/mbo_utils.py`, nie aus `datetime.now()`.
- Turtle wird deterministisch geschrieben (sortiert, keine Blank Nodes in generierten Graphen).
- Netzwerk nur in `step_fetch.py` (`python main.py fetch`), nie im Standardlauf.
- Behauptungen belegen: jede Aussage trägt `dct:source`; was nicht belegt ist, heißt `seed`. Keine Werte erfinden.
- Kommunikation mit Flo auf Deutsch (du); Repo, Code, Ontologie, README, Doku auf British English; Abbildungen englisch, ohne Kopf-/Fußzeile, Kantenlabels als gelbe Chips (#fbbf24) in der Mitte des Pfeils; Mermaid im festgelegten Farbschema.
- Windows cmd: zusammengehörige Befehle in **einer** Zeile mit `&&`; `call` vor `.venv\Scripts\activate`.
- Ontologie nicht als LEGO-offiziell bezeichnen; Marke nur zur Identifikation.

## A4 Beschlusslage

| Frage | Beschluss | seit |
|---|---|---|
| Repo-Name | `minimal-brick-ontology` unter Research-Squirrel-Engineers | 2026-11-18 |
| Namespace | `https://w3id.org/mbo/` (Ontologie `…/ontology#`, Thesaurus `…/thesaurus/`, Beispiel `…/example/`, Quellen `…/source/`) | 2026-11-18 |
| CRM-Anbindung | CIDOC CRM Kern + CRMdig + CRMba (nicht CRMarchaeo, nicht CRMsci) | 2026-11-18 |
| Farbquelle | erst WebFetch, sonst cmd-Skript: WebFetch scheiterte, daher `main.py fetch` (Rebrickable CSV) | 2026-11-18 |
| Umfang | Steine, Platten, Minifiguren (Körperteile), alle Farben; Fliesen und Grundplatten zusätzlich im Seed | Vorschlag 2026-11-18 |
| Sprachen | Labels en (Pflicht) + de (Kategorien, Merkmale, Einheiten); Farben/Teile nur en | Vorschlag 2026-11-18 |
| Konzept-IRIs | Farben per Namens-Slug (`colour/white`), Teile per Teilenummer (`part/3001`); stabil trotz wechselnder Quellen | Vorschlag 2026-11-18 |
| Geometrie | Rastereinheiten (Noppen, Plattenhöhen) als Kern, Millimeter nur abgeleitet und als nominal markiert | Vorschlag 2026-11-18 |
| Verifikationsstatus | `sourced`, `seed`, `rebrickable`, `derived` | Vorschlag 2026-11-18 |
| Druckvarianten | Teile mit `pr`/`pb` in der Nummer sind nicht im Umfang | Vorschlag 2026-11-18 |
| DCAT-AP | Version 3.0; eigener Subset-SHACL, offizielle Shapes vor Portal-Einreichung zusätzlich | Vorschlag 2026-11-18 |
| Lizenz | Vokabular/Daten/Doku CC BY 4.0, Code MIT | Vorschlag 2026-11-18 |

## A5 Was in welchem Chat hochgeladen wird

Standard-Bundle (nur versionierte Dateien, eine Zeile, aus dem Repo-Ordner):

    git archive --format=zip --output=..\mbo-upload.zip HEAD

Dazu `PRIMER.md` extra, falls geändert. Nicht hochladen: `.venv\`, `.git\`.
Für den Rekonstruktions-Chat: das Bundle plus die Build-Spec (`aenderungen.json`) bzw. ein Spec nach dem Docstring von `py/mbo_build.py`.

## A6 IRI-Landkarte

| Pfad | Inhalt | Ziel des Redirects | Status |
|---|---|---|---|
| `/` | Startseite | `index.html` | beschlossen |
| `/ontology` | OWL (Fragmente `#Piece`) | `ontology.ttl` / `.html` | beschlossen |
| `/thesaurus/…` | Schemata und Konzepte | `thesaurus.ttl` / `thesaurus.html#<scheme>/<id>` | beschlossen |
| `/example/…` | Beispiel | `example-pyramid.ttl` | beschlossen |
| `/catalogue`, `/dataset/…`, `/distribution/…` | DCAT-AP | `catalogue.ttl` | beschlossen |
| `/shapes` | SHACL | `mbo-shapes.ttl` | beschlossen |

Offene Fragen: w3id-PR noch nicht gestellt (`w3id/README.md`); Kontakt-Handle in `w3id/mbo/README.md` fehlt; Content Negotiation nur für `text/turtle`.

# Teil B — Schrittübersicht

| ID | Schritt | Repo | hängt ab von | Status |
|---|---|---|---|---|
| S0 | Festlegungen (Name, Namespace, CRM, Farbquelle) | mbo | – | erledigt 2026-11-18 |
| S1 | Gerüst: main.py, utils, Lizenz, CITATION | mbo | S0 | erledigt 2026-11-18 |
| S2 | Ontologie, Seed-Thesaurus, SHACL, DCAT-AP, Beispiel, Doku-Seite | mbo | S1 | erledigt 2026-11-18 |
| S3 | Rebrickable laden (`main.py fetch`), alle Farben/Teile bauen | mbo | S2 | offen |
| S4 | w3id-PR stellen, GitHub-Repo anlegen, Pages aktivieren | mbo | S2 | offen |
| S5 | Integration in den Rekonstruktions-Chat (Spec aus `aenderungen.json`) | mbo + Skill | S2 | offen |
| S6 | Offizielle LEGO-Farbtabelle 2010 einpflegen, LEGO-Farb-IDs ergänzen | mbo | S3 | offen |
| S7 | CRM-Alignment gegen RDFS prüfen, offizielle DCAT-AP-Shapes laufen lassen | mbo | S2 | offen |
| S8 | Alignments: Wikidata, Getty AAT (optional) | mbo | S3 | offen |

S3 und S5 sind unabhängig; S4 kann jederzeit nach S2. S6 braucht die Rebrickable-Farben aus S3, damit Zuordnungen per Namen greifen.

# Teil C — Die Schritte

## S3 — Rebrickable laden

**Ziel:** Alle Farben (mit Hex) und alle Steine/Platten/Fliesen/Minifigurenteile im Thesaurus.

**Uploads:** Standard-Bundle.

Befehl (eine Zeile): `python main.py fetch && python main.py`. `fetch` lädt `colors`, `part_categories`, `parts`
nach `data/raw/rebrickable/` und schreibt `FETCHED.txt` (URL, Größe, SHA-256, Last-Modified). Der Standardlauf gleicht Seed-Farben
über den normalisierten Namen ab (grey/gray), ersetzt Seed-Hex durch Rebrickable-Hex (Notiz am Konzept) und bestätigt Seed-Teile.
Gedacht: Rebrickable-Kategorien mit Präfix Brick/Plate/Tile/Baseplate werden Zwischenebenen unter den MBO-Kategorien.

**Abnahme:** `RESULT OK`; `colours.csv` hat > 150 Zeilen und keine Farbe mit `hex_status=seed`, die in Rebrickable vorkommt;
Bericht nennt, welche Seed-Teile nicht in `parts.csv` stehen; zwei Läufe, `git status` sauber.

## S4 — w3id und GitHub

**Ziel:** Die IRIs lösen auf.

Repo anlegen, Pages auf `docs/` stellen, `w3id/mbo/` per PR in `perma-id/w3id.org` (siehe `w3id/README.md`).
**Abnahme:** `curl -sIL -H "Accept: text/turtle" https://w3id.org/mbo/ontology` endet bei `ontology.ttl` mit 200.

## S5 — Rekonstruktions-Chat

**Ziel:** Der KIRI-Workflow schreibt zusätzlich eine Build-Spec und daraus RDF.

`aenderungen.json` enthält Ebenen, Breiten, Farben und Steinzahlen; daraus `layers[].pieces[]` ableiten und `py/mbo_build.py` aufrufen.
**Abnahme:** `python py/mbo_build.py spec.json out.ttl` läuft für beide bisherigen Modelle; SHACL bleibt grün.

# Teil D — Offene Punkte

- Lizenz der Rebrickable-Dateien prüfen, bevor `data/raw/rebrickable/` veröffentlicht wird (Quellenbeschreibung sagt „any purpose“; Originalbedingungen lesen).
- LEGO-Farb-IDs fehlen für Farben außerhalb der Seed-Tabelle (S6).
- Minifiguren-Kopfbedeckung: Kategorie vorhanden, noch kein Teil im Seed.
- Soll `Element` (Design × Farbe) mit LEGO-Element-IDs im Thesaurus aufgezählt werden? Quelle `elements.csv` wäre groß; bisher nur im Beispiel on demand.
- E54-Dimensionen nach CRM-Muster (P43) statt Kurzeigenschaften `studsLength` usw.?
- ORCID in `CITATION.cff` und Kontakt-Handle in `w3id/mbo/README.md` eintragen.
