"""
ingest_movies.py — Entry-point for the FilmInsight ingestion pipeline (unified).

Usage:
------
    python -m ingestion.ingest_movies
    # or
    python ingestion/ingest_movies.py
"""

from __future__ import annotations

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

from app.services.ingestion_service import IngestionService
from app.db.database import SessionLocal
from app.models.movie_script import MovieScript

def run() -> None:
    print("=" * 60)
    print("  FilmInsight — Unified Ingestion Pipeline")
    print("=" * 60)

    db = SessionLocal()
    svc = IngestionService()

    # Heal status: check if any READY movie in PostgreSQL actually has 0 vectors in Chroma.
    # If so, reset its status to UPLOADED so it gets re-ingested.
    print("Checking Chroma DB consistency with PostgreSQL...")
    all_scripts = db.query(MovieScript).all()
    for s in all_scripts:
        try:
            res = svc._get_chroma_collection().get(where={"movie_name": s.title}, limit=1)
            ids = res.get("ids", [])
            if not ids or len(ids) == 0:
                if s.status == "READY":
                    print(f"Movie '{s.title}' is marked READY in DB but has 0 vectors in Chroma. Resetting to UPLOADED.")
                    s.status = "UPLOADED"
                    db.commit()
        except Exception as e:
            print(f"Error checking consistency for '{s.title}': {e}")

    # Query scripts with UPLOADED, PROCESSING, or FAILED status
    scripts = db.query(MovieScript).filter(
        MovieScript.status.in_(["UPLOADED", "PROCESSING", "FAILED"])
    ).all()

    if not scripts:
        print("No scripts to process.")
        return

    print(f"Found {len(scripts)} script(s) to process.")

    success_count = 0
    failure_count = 0

    for script in scripts:
        print(f"\nProcessing '{script.title}' (id={script.id})...")
        
        # Mark as PROCESSING
        script.status = "PROCESSING"
        db.commit()

        # Determine source file
        supabase_filename = script.supabase_path
        local_path = PROJECT_ROOT / "movie_scripts" / (script.file_path or f"{script.title}.pdf")
        
        try:
            if supabase_filename:
                chunks = svc.ingest_movie(
                    movie_name=script.title,
                    movie_id=script.id,
                    supabase_filename=supabase_filename
                )
            elif local_path.exists():
                chunks = svc.ingest_movie(
                    movie_name=script.title,
                    movie_id=script.id,
                    local_pdf_path=local_path
                )
            else:
                raise ValueError(f"No source PDF found. Supabase path is null and local file '{local_path}' does not exist.")

            # Mark as READY
            script.status = "READY"
            script.chunks_stored = chunks
            script.ingested_at = datetime.utcnow()
            script.ingestion_error = None
            db.commit()
            success_count += 1
            print(f"[OK] '{script.title}' successfully ingested.")

        except Exception as exc:
            db.rollback()
            error_msg = str(exc)[:1000]
            script.status = "FAILED"
            script.ingestion_error = error_msg
            db.commit()
            failure_count += 1
            print(f"[FAIL] Failed to ingest '{script.title}': {error_msg}")

    print("\n" + "=" * 60)
    print(f"Ingestion completed. {success_count} succeeded, {failure_count} failed.")
    print("=" * 60)

if __name__ == "__main__":
    run()
