import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript

def backup_movie_scripts():
    backup_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "movie_scripts_backup.json"))
    with Session(engine) as db:
        movies = db.query(MovieScript).all()
        data = []
        for m in movies:
            data.append({
                "id": m.id,
                "title": m.title,
                "file_path": m.file_path,
                "status": m.status,
                "chunks_stored": m.chunks_stored,
                "uploaded_at": m.uploaded_at.isoformat() if getattr(m, "uploaded_at", None) else None,
                "tmdb_id": m.tmdb_id,
                "poster_url": m.poster_url,
                "backdrop_url": m.backdrop_url,
                "overview": m.overview,
                "genres": m.genres,
                "runtime": m.runtime,
                "rating": m.rating,
                "release_date": m.release_date
            })
        
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Backup successful! Saved {len(data)} records to {backup_path}")

if __name__ == "__main__":
    backup_movie_scripts()
