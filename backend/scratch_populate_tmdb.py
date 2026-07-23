import asyncio
import os
import sys

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.tmdb import fetch_movie_metadata

async def populate_tmdb():
    print("Starting TMDB metadata backfill...")
    with Session(engine) as db:
        # Find all scripts that don't have a tmdb_id or poster_url
        scripts = db.query(MovieScript).filter(MovieScript.poster_url == None).all()
        
        if not scripts:
            print("All movies already have TMDB metadata.")
            return

        print(f"Found {len(scripts)} movies needing TMDB metadata.")

        for script in scripts:
            print(f"Fetching metadata for '{script.title}'...")
            try:
                metadata = await fetch_movie_metadata(script.title)
                if metadata:
                    script.poster_url = metadata.get("poster_url")
                    script.backdrop_url = metadata.get("backdrop_url")
                    script.tmdb_id = metadata.get("tmdb_id")
                    script.overview = metadata.get("overview")
                    script.release_date = metadata.get("release_date")
                    script.genres = metadata.get("genres")
                    script.runtime = metadata.get("runtime")
                    script.rating = metadata.get("rating")
                    
                    db.commit()
                    print(f"  -> Successfully updated '{script.title}' (TMDB ID: {script.tmdb_id})")
                else:
                    print(f"  -> No TMDB metadata found for '{script.title}'")
            except Exception as e:
                print(f"  -> Error updating '{script.title}': {e}")
                db.rollback()

if __name__ == "__main__":
    asyncio.run(populate_tmdb())
    print("Backfill complete.")
