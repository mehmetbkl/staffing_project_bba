"""
app.py - StaffCast Dashboard.

Start:
    pip install -r requirements.txt
    python app.py
"""

from __future__ import annotations
import logging, os, sys
import dash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = dash.Dash(
    __name__,
    title="StaffCast",
    assets_folder="assets",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"charset": "utf-8"},
    ],
)

from layouts.dashboard import render_app_layout
from callbacks.weather_callbacks import register_weather_callbacks
from callbacks.chart_callbacks import register_chart_callbacks
from callbacks.ui_callbacks import register_ui_callbacks

app.layout = render_app_layout()

register_weather_callbacks(app)
register_chart_callbacks(app)
register_ui_callbacks(app)

server = app.server

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "true").lower() == "true"
    logger.info("StaffCast -> http://localhost:%d", port)
    app.run(debug=debug, port=port)