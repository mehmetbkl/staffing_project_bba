#!/usr/bin/env bash
# =============================================================================
# scripts/run_etl.sh
# Täglicher voller Lauf der Staffing-Pipeline:
#   1. ETL  – Roh-Daten holen + laden (Library, Wetter, Holidays)
#             und gold.feature_store bauen   (python -m etl.pipeline)
#   2. Prognose – saisonale Baseline nach gold.predictions
#             + gold.staffing_recommendations (models(Nico)/baseline_forecast.py)
#
# Wird per launchd/cron um 00:00 ausgeführt (siehe scripts/README.md).
# Läuft dort, wo DB-Zugriff (NeonDB) besteht – nicht im Cowork-Sandbox.
# =============================================================================

set -euo pipefail

# Projekt-Root = ein Verzeichnis über diesem Skript, robust gegen Aufrufort.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Log-Verzeichnis + zeitgestempelte Logdatei
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/etl_$(date +%Y%m%d).log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# Python wählen: venv bevorzugt, sonst python3 aus PATH.
if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PY="$PROJECT_ROOT/.venv/bin/python"
elif [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
    PY="$PROJECT_ROOT/venv/bin/python"
else
    PY="$(command -v python3 || true)"
fi

if [[ -z "${PY:-}" ]]; then
    log "FEHLER: Kein Python gefunden (.venv, venv oder python3)."
    exit 1
fi

# .env muss vorhanden sein (DATABASE_URL_ETL etc.)
if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    log "FEHLER: .env nicht gefunden – DB-Zugang fehlt."
    exit 1
fi

log "=== Pipeline-Lauf gestartet (Python: $PY) ==="

# 1. ETL + Gold-Feature-Store
log "Schritt 1/2: ETL + Feature-Store ..."
if "$PY" -m etl.pipeline >>"$LOG_FILE" 2>&1; then
    log "Schritt 1/2 OK."
else
    log "FEHLER in Schritt 1/2 (ETL). Abbruch."
    exit 1
fi

# 2. Baseline-Prognose -> gold.predictions + staffing_recommendations
log "Schritt 2/2: Baseline-Prognose ..."
if "$PY" "models(Nico)/baseline_forecast.py" >>"$LOG_FILE" 2>&1; then
    log "Schritt 2/2 OK."
else
    log "FEHLER in Schritt 2/2 (Prognose). ETL-Daten sind dennoch aktualisiert."
    exit 1
fi

log "=== Pipeline-Lauf erfolgreich abgeschlossen ==="

# Alte Logs (> 30 Tage) aufräumen
find "$LOG_DIR" -name 'etl_*.log' -type f -mtime +30 -delete 2>/dev/null || true
