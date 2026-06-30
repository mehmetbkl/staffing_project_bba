# Geplanter ETL-Lauf (täglich 00:00)

Aktualisiert die NeonDB automatisch jede Nacht:

1. **ETL** – holt Library-, Wetter- und Feiertagsdaten und baut `gold.feature_store`
   (`python -m etl.pipeline`).
2. **Prognose** – saisonale Baseline schreibt `gold.predictions` und
   `gold.staffing_recommendations` (`models(Nico)/baseline_forecast.py`).

Danach ist das Dashboard ohne manuelles Zutun aktuell.

> Läuft auf **deinem Mac** (dort ist DB-Zugriff vorhanden). Der Cowork-Sandbox
> erreicht die NeonDB nicht und kann den Lauf nicht selbst ausführen.

---

## Voraussetzungen

- Abhängigkeiten installiert (am besten in einem venv im Projekt-Root):

  ```bash
  cd "<Projekt-Root>"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

  Das Skript nutzt automatisch `.venv/bin/python` bzw. `venv/bin/python`,
  sonst das `python3` aus dem PATH.

- `.env` im Projekt-Root mit gültigen DB-URLs (`DATABASE_URL_ETL`,
  idealerweise auch `DATABASE_URL_DS`).

---

## Manuell testen (vor dem Einplanen)

```bash
cd "<Projekt-Root>"
bash scripts/run_etl.sh
cat logs/etl_$(date +%Y%m%d).log
```

Erwartung: „Pipeline-Lauf erfolgreich abgeschlossen". Logs liegen in `logs/`.

---

## Als täglichen Job einrichten (macOS / launchd)

```bash
# 1. plist in den LaunchAgents-Ordner kopieren
cp scripts/com.staffing.etl.plist ~/Library/LaunchAgents/

# 2. Job laden (aktivieren)
launchctl load ~/Library/LaunchAgents/com.staffing.etl.plist

# Status prüfen
launchctl list | grep com.staffing.etl

# Einmal sofort testweise starten (ohne auf 00:00 zu warten)
launchctl start com.staffing.etl
```

Deaktivieren / entfernen:

```bash
launchctl unload ~/Library/LaunchAgents/com.staffing.etl.plist
rm ~/Library/LaunchAgents/com.staffing.etl.plist
```

> **Wichtig:** Die plist enthält absolute Pfade auf den aktuellen Projektort.
> Wenn du das Repo verschiebst, passe die Pfade in
> `scripts/com.staffing.etl.plist` an und lade den Job neu.
> launchd startet den Job nur, wenn der Mac um 00:00 läuft (Sleep zählt nicht);
> verpasste Läufe lassen sich morgens mit `launchctl start com.staffing.etl`
> nachholen.

---

## Alternative: cron

```bash
crontab -e
# Zeile hinzufügen (täglich 00:00):
0 0 * * * /bin/bash "<Projekt-Root>/scripts/run_etl.sh"
```

---

## Logs

- `logs/etl_YYYYMMDD.log` – Lauf-Protokoll (Schritte + Pipeline-Ausgabe).
- `logs/launchd.out.log` / `logs/launchd.err.log` – launchd-Ausgabe.
- Logs älter als 30 Tage werden automatisch gelöscht.
