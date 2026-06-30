import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_ETL= os.environ.get("DATABASE_URL_ETL")

LIBRARY_LAT=float(os.environ.get("LIBRARY_LAT", 49.7806))
LIBRARY_LON=float(os.environ.get("LIBRARY_LON", 9.9718))
LIBRARY_NAME=os.environ.get("LIBRARY_NAME", "Stadtteilbücherei Hubland Würzburg")