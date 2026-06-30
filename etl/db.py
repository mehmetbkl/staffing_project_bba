import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.environ.get("DATABASE_URL_ETL"))

def test_connection():
    with engine.connect() as conn:
        row = conn.execute(text("SELECT current_user, current_database()")).fetchone()
        print(f"User: {row[0]} | DB: {row[1]}")

if __name__ == "__main__":
    test_connection()