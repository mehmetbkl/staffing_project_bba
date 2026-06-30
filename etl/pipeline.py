from etl.sources.library  import fetch_all as fetch_library
from etl.sources.weather  import fetch_all as fetch_weather
from etl.sources.holidays import fetch_all as fetch_holidays
from etl.loaders.postgres import load_library, load_weather, load_holidays
from etl.transformers.gold_features import build_feature_store

def run():
    print("Library...")
    load_library(fetch_library())

    print("Weather...")
    load_weather(fetch_weather())

    print("Holidays...")
    load_holidays(fetch_holidays())

    # Gold-Layer: Roh-/Processed-Daten zu stündlichem Feature-Store verknüpfen
    print("Feature-Store (Gold)...")
    build_feature_store()

    print("Pipeline done.")

if __name__ == "__main__":
    run()