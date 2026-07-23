import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from app.db.database import engine

def inspect_table():
    inspector = inspect(engine)
    columns = inspector.get_columns('movie_requests')
    for col in columns:
        print(f"Column: {col['name']} - {col['type']}")

if __name__ == "__main__":
    inspect_table()
