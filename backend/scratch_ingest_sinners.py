import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.ingestion_service import IngestionService

def ingest_sinners():
    with Session(engine) as db:
        script = db.query(MovieScript).filter(MovieScript.title == "Sinners").first()
        if not script:
            print("Sinners not found in DB.")
            return
            
        print(f"Found Sinners with ID: {script.id}")
        
        ingestion = IngestionService()
        try:
            chunks = ingestion.ingest_from_supabase("Sinners2025.pdf", movie_id=script.id)
            print(f"Successfully ingested {chunks} chunks for Sinners.")
        except Exception as e:
            print(f"Ingestion failed: {e}")

if __name__ == "__main__":
    ingest_sinners()
