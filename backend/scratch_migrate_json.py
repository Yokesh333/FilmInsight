import os
import sys
import json
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.tmdb import fetch_movie_metadata

async def migrate():
    processed_file = r"C:\Users\Yokesh\Downloads\FilmInsight_AI\ingestion\processed_movies.json"
    if not os.path.exists(processed_file):
        print("processed_movies.json not found!")
        return

    with open(processed_file, "r") as f:
        legacy_data = json.load(f)

    imported = 0
    skipped = 0
    failed_tmdb = 0

    print(f"Found {len(legacy_data)} movies in legacy JSON.")

    with Session(engine) as db:
        for title, info in legacy_data.items():
            # Check if exists (case-insensitive or just exact match)
            # The JSON has titles like "500 Days Of Summer", "Batman Begins"
            existing = db.query(MovieScript).filter(MovieScript.title.ilike(title)).first()
            if existing:
                print(f"Skipping '{title}' - already in database.")
                skipped += 1
                continue
            
            print(f"Importing '{title}'...")
            
            # Create the record first
            script = MovieScript(
                title=title,
                file_path=info.get("pdf_path", ""),
                status="ingested",  # they are already in ChromaDB!
                chunks_stored=info.get("chunks_stored", 0)
            )
            
            # Fetch TMDB metadata
            metadata = await fetch_movie_metadata(title)
            if metadata:
                script.tmdb_id = metadata.get("tmdb_id")
                script.poster_url = metadata.get("poster_url")
                script.backdrop_url = metadata.get("backdrop_url")
                script.overview = metadata.get("overview")
                script.genres = metadata.get("genres")
                script.runtime = metadata.get("runtime")
                script.rating = metadata.get("rating")
                script.release_date = metadata.get("release_date")
                
                # If poster is missing, we consider it failed TMDB lookup for our tracking
                if not script.poster_url:
                    failed_tmdb += 1
            else:
                failed_tmdb += 1

            db.add(script)
            imported += 1
            
            # Commit one by one to avoid losing everything on failure
            db.commit()

    print("\n--- Migration Complete ---")
    print(f"Movies Imported: {imported}")
    print(f"Movies Skipped: {skipped}")
    print(f"Movies that failed TMDB lookup: {failed_tmdb}")

if __name__ == "__main__":
    asyncio.run(migrate())
