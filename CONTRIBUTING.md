# Guidelines

## Branching-Strategie

* `main` → stabiler Code (immer deploybar)
* `dev` → Integrations-Branch
* Feature-Branches:

  * `feature/<name>`
  * `bugfix/<name>`
  * `hotfix/<name>`

  Direkte Commits auf `main`sind nicht erlaubt.

---

## Commit Messages

Wir verwenden klare, strukturierte Commit-Nachrichten:

Format:
type(scope): kurze Beschreibung

Beispiele:

* feat(data): add dataset
* fix(model): correct prediction error
* docs(readme): update instructions

Typen:

* feat → neues Feature
* fix → Bugfix
* docs → Dokumentation
* refactor → Code-Verbesserung ohne Feature
* test → Tests

---

## Pull Requests

* Jeder PR muss:

  * verständlich beschrieben sein
  * einen klaren Zweck haben
  * klein und fokussiert sein

* Mindestens 1 Review erforderlich
* Keine direkten Commits auf `main`

---

## Datenmanagement

* Rohdaten → data/raw/
* Verarbeitete Daten → data/processed/
* Rohdaten werden nicht überschrieben
* Datenquellen werden dokumentiert

---

## Code Style

* Einheitlicher Stil (z. B. mit Black)
* Verständliche und sprechende Variablennamen
* Wiederverwendbarer Code wird ausgelagert
* Code soll lesbar und nachvollziehbar sein

---

### Reproduzierbarkeit

Das Projekt muss von Dritten ausführbar sein:
    1. Repository klonen
    2. Dependencies installieren (pip install -r requirements.txt)
    3. Notebooks ausführen

Alle benötigten Libraries müssen in requirements.txt enthalten sein.

---

## Dependencies

* Nur notwendige Libraries hinzufügen
* Regelmäßig Updates prüfen

---

## Sicherheit

* Keine Secrets im Code (`.env` verwenden)
* `.env` niemals committen
* Sensible Daten immer anonymisieren

---

## Allgemeine Regeln

* "Works on my machine" ist kein akzeptabler Zustand
* Code muss für andere verständlich sein
* Lieber einfache Lösungen als unnötig komplexe

---

## Was ausgeschlossen wird

* Daten (niemals committen)
  data/raw/
  .csv
  .xlsx
  .parquet
 
* Notebook Outputs
  .ipynb_checkpoints/
  /.ipynb_checkpoints/
 
* Python
  __pycache__/
  .pyc
  .pyo
  venv/
  .env
 
* Betriebssystem
  .DS_Store
  Thumbs.db
 
* IDE
  .vscode/
  .idea/

---
