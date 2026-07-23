"""
check_pdf_sources.py
Check that every FAILED movie has a usable PDF source before starting ingestion.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript

TRUE_FAILED = [
    "Frankenstein","Hamnet","Interstellar","Memento","Oppenheimer",
    "Project Hail Mary","Superman","Tenet","The Dark Knight Rises",
    "The Dark Knight","The Prestige",
]

project_root = Path(__file__).resolve().parent.parent

with Session(engine) as db:
    print(f"\n{'Title':<35} {'supabase_path':<45} {'local_exists'}")
    print("-" * 100)
    for title in TRUE_FAILED:
        s = db.query(MovieScript).filter(MovieScript.title == title).first()
        if not s:
            print(f"{title:<35} NOT IN DB")
            continue
        supa = s.supabase_path or ""
        fp   = s.file_path or ""
        local_path = project_root / "movie_scripts" / fp if fp else None
        local_ok = "YES" if local_path and local_path.exists() else "NO"
        print(f"{title:<35} {supa:<45} local={local_ok} (file_path={fp})")
