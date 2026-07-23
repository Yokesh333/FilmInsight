import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.database import engine

def add_columns():
    with engine.connect() as conn:
        columns = [
            "poster_url VARCHAR",
            "backdrop_url VARCHAR",
            "tmdb_id INTEGER",
            "overview TEXT",
            "release_date VARCHAR",
            "genres VARCHAR",
            "runtime INTEGER",
            "rating FLOAT"
        ]
        for col in columns:
            col_name = col.split()[0]
            try:
                conn.execute(text(f"ALTER TABLE movie_scripts ADD COLUMN {col}"))
                print(f"Added column {col_name}")
            except Exception as e:
                # Column might already exist
                print(f"Skipping {col_name}, might already exist: {e}")
        conn.commit()

if __name__ == "__main__":
    add_columns()
    print("Database alteration complete.")
