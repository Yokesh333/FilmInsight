import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.tmdb import fetch_movie_metadata

async def fix_typos():
    updates = {
        "Openheimer": "Oppenheimer",
        "Spiderman No Way Home": "Spider-Man: No Way Home"
    }

    with Session(engine) as db:
        for old_title, new_title in updates.items():
            script = db.query(MovieScript).filter(MovieScript.title == old_title).first()
            if not script:
                print(f"Skipping {old_title}, not found in DB.")
                continue
            
            print(f"Updating '{old_title}' to '{new_title}'...")
            
            # 1. Update title
            script.title = new_title
            
            # 2. Fetch metadata
            metadata = await fetch_movie_metadata(new_title)
            if metadata:
                script.tmdb_id = metadata.get("tmdb_id")
                script.poster_url = metadata.get("poster_url")
                script.backdrop_url = metadata.get("backdrop_url")
                script.overview = metadata.get("overview")
                script.genres = metadata.get("genres")
                script.runtime = metadata.get("runtime")
                script.rating = metadata.get("rating")
                script.release_date = metadata.get("release_date")
                print(f"  -> Successfully fetched metadata for {new_title}. Poster: {script.poster_url}")
            else:
                print(f"  -> Failed to fetch metadata for {new_title}")
            
            db.commit()
            print(f"Committed changes for {new_title}.\n")

if __name__ == "__main__":
    asyncio.run(fix_typos())
