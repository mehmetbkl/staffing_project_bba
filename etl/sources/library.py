import requests
import pandas as pd

BASE_URL = "https://opendata.wuerzburg.de/api/explore/v2.1/catalog/datasets"
DATASET  = "besucherzahlen-stadtteilbuecherei-hubland"

def fetch(limit=100, offset=0):
    url = f"{BASE_URL}/{DATASET}/records"
    params = {
        "limit":    limit,
        "offset":   offset,
        "order_by": "timestamp asc",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# Opendatasoft erlaubt offset+limit <= 10000. Sicherheitskappe, damit die
# Pagination unter keinen Umstaenden endlos laeuft (verhinderter Job-Timeout).
MAX_OFFSET = 10_000


def fetch_all():
    records = []
    offset  = 0
    limit   = 100

    while offset < MAX_OFFSET:
        data  = fetch(limit=limit, offset=offset)
        batch = data.get("results", [])
        if not batch:
            break
        records.extend(batch)
        offset += limit

    df = pd.DataFrame(records)[["timestamp", "count_enter", "count_exit"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Europe/Berlin")
    return df

if __name__ == "__main__":
    df = fetch_all()
    from etl.loaders.postgres import load_library
    load_library(df)