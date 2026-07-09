# Prüfbericht – UI/UX & Nacht-Cron (07.07.2026)

## Zusammenfassung

| Bereich | Status |
|---|---|
| Dashboard startet (Demo-Modus) | ✅ läuft fehlerfrei |
| Alle 5 Seiten rendern (hell + dunkel) | ✅ kein Fehler |
| Dark-Mode Charts **Historie** | ⚠️ Bug: kein Live-Umschalten |
| GitHub-Actions Nacht-Cron | ❌ schlägt jede Nacht fehl (Secrets fehlen) |
| Lokaler launchd-Cron (`scripts/`) | ✅ entfernt (war obsolet) |

---

## 1. UI/UX

Das Dashboard bootet sauber (`python app.py`, HTTP 200) und fällt ohne DB
korrekt in den Demo-Modus. Alle fünf Seiten – Dashboard, Prognose, Historie,
Personalplanung, Modell-Insights – rendern in **beiden** Themes ohne Exception.
Routing (`ui_callbacks.route`) und Sidebar sind konsistent mit `NAV_ITEMS`.
Theme-Toggle, Auto-Refresh der Schichtübersicht und Info-Modal sind sauber
verdrahtet.

### Gefundener Bug: Dark-Mode auf der Historie-Seite

Auf **Prognose** wird der Chart bei Theme-Wechsel neu eingefärbt
(`chart_callbacks.py` reagiert auf `theme-store`). Auf **Historie** passiert das
**nicht**: die vier Plotly-Charts bekommen das Theme nur beim Seitenaufruf
(`route()` → `State("theme-store")`). Schaltet man auf der Historie-Seite auf
Dunkelmodus, bleiben die Charts hell, bis man weg- und zurücknavigiert.

Ursache: Die `dcc.Graph` in `layouts/history_page.py` haben **keine `id`**, also
kann kein Callback sie umfärben. Der Kommentar in `utils/chart_theme.py`
beschreibt genau dieses Verhalten – es ist für die Historie aber nie umgesetzt.

**Fix-Optionen:**
- Den vier `dcc.Graph` feste `id`s geben und in `chart_callbacks.py` einen
  Callback ergänzen, der bei `theme-store`-Änderung die Historie-Figuren neu
  baut (analog zum Forecast-Chart). Sauberste Lösung.
- Alternativ: die Historie-Seite bei Theme-Wechsel neu rendern lassen.

### Kleinere Hinweise (kein Blocker)
- `utils/constants.py` (`LIBRARY_LAT/LON` = 49.7913 / 9.9534) weicht von
  `.env.example` (49.7806 / 9.9718) ab – für Konsistenz angleichen.
- Es liegen **nicht committete** UI-Änderungen im Repo (u. a. neue Dateien
  `assets/zzz-polish.css`, `utils/chart_theme.py` sowie geänderte Layout-/
  Callback-Dateien). Der letzte UI-Stand ist noch nicht gepusht.

> Live-Klickdurchlauf im Browser: Der Localhost lief zum Prüfzeitpunkt nicht.
> Zum Starten auf deinem Mac: `cd dashboard && python app.py` → http://localhost:8050

---

## 2. Nacht-Cron (GitHub Actions)

Der Workflow `.github/workflows/etl.yml` ist **aktiv** und läuft planmäßig
(`0 22 * * *` UTC = 00:00 MESZ). Alle referenzierten Dateien und die
Secret-Zuordnung im YAML sind korrekt.

**Aber: Alle 7 bisherigen Läufe sind fehlgeschlagen.** Fehler im ETL-Schritt:

```
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from string ''
```

Ursache: `DATABASE_URL_ETL` ist im Runner leer. Unter
*Settings → Secrets and variables → Actions* steht: **"This repository has no
secrets."** Die im Workflow referenzierten Secrets `DATABASE_URL_ETL` und
`DATABASE_URL_DS` sind schlicht nicht gesetzt.

**Fix (musst du selbst machen – ich gebe keine DB-Zugangsdaten ein):**
GitHub → Repo → Settings → Secrets and variables → Actions → *New repository
secret* und anlegen:
- `DATABASE_URL_ETL` = NeonDB-URL (ETL-User)
- `DATABASE_URL_DS`  = NeonDB-URL (DS-User)

Danach `Re-run jobs` auf dem letzten fehlgeschlagenen Lauf → grün prüfen.

Kleiner Hinweis: Der Cron ist auf MESZ (Sommerzeit) fixiert. Im Winter läuft er
um 23:00 Ortszeit. Bei Bedarf zwei Cron-Zeilen (`0 22` und `0 23`) eintragen.

---

## 3. Lokaler launchd-Cron entfernt

Der Ordner `scripts/` (run_etl.sh, com.staffing.etl.plist, README.md) wurde
gelöscht, da laut Absprache obsolet und durch die GitHub Action ersetzt. Es gab
keine Referenzen darauf außerhalb des Ordners.
