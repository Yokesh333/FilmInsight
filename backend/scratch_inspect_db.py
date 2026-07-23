import os
import sys

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript

def inspect_db():
    with Session(engine) as db:
        total = db.query(MovieScript).count()
        with_poster = db.query(MovieScript).filter(MovieScript.poster_url != None).count()
        without_poster = db.query(MovieScript).filter(MovieScript.poster_url == None).count()
        
        print(f"Total movies: {total}")
        print(f"With poster: {with_poster}")
        print(f"Without poster: {without_poster}")
        
        print("\nAll movies:")
        movies = db.query(MovieScript).all()
        for m in movies:
            poster = "YES" if m.poster_url else "NO"
            print(f"- {m.title} (Status: {m.status}, Poster: {poster})")

if __name__ == "__main__":
    inspect_db()
