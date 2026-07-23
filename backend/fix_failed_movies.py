"""
fix_failed_movies.py
─────────────────────────────────────────────────────────────────────
Two-phase repair for movies in bad state after audit:

Phase 1 — Stale FAILED (have Chroma embeddings, DB says FAILED)
    → Just update DB status to READY. No re-ingestion needed.
    Movies: Beauty And The Beast, Deadpool & Wolverine, Dunkirk

Phase 2 — True FAILED (no Chroma embeddings, DB says FAILED)
    → Full re-ingestion via IngestionService.
    Movies: Frankenstein, Hamnet, Interstellar, Memento, Oppenheimer,
            Project Hail Mary, Superman, Tenet, The Dark Knight Rises,
            The Dark Knight, The Prestige

Run from backend/ directory with the venv active:
    python fix_failed_movies.py
"""

import os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.rag_service import _get_chroma_collection

# ── Phase 1: Stale-FAILED movies (embeddings exist, DB wrong) ─────────────────
STALE_FAILED = [
    "Beauty And The Beast",
    "Deadpool & Wolverine",
    "Dunkirk",
]

# ── Phase 2: True-FAILED movies (need full re-ingestion) ─────────────────────
TRUE_FAILED = [
    "Frankenstein",
    "Hamnet",
    "Interstellar",
    "Memento",
    "Oppenheimer",
    "Project Hail Mary",
    "Superman",
    "Tenet",
    "The Dark Knight Rises",
    "The Dark Knight",
    "The Prestige",
]


def verify_chroma(movie_name: str) -> int:
    """Return number of Chroma chunks for this movie_name."""
    try:
        col = _get_chroma_collection()
        results = col.get(where={"movie_name": movie_name})
        return len(results["ids"])
    except Exception as e:
        print(f"    [!] Chroma verify error: {e}")
        return -1


def phase1_fix_stale_failed():
    """Phase 1: update DB status to READY for stale-FAILED movies."""
    print("\n" + "=" * 70)
    print("PHASE 1 — Fixing stale-FAILED movies (embeddings exist, DB wrong)")
    print("=" * 70)

    with Session(engine) as db:
        for title in STALE_FAILED:
            chunks = verify_chroma(title)
            script = db.query(MovieScript).filter(MovieScript.title == title).first()
            if not script:
                print(f"  SKIP  '{title}' — not found in DB")
                continue
            if chunks <= 0:
                print(f"  SKIP  '{title}' — Chroma now reports {chunks} chunks, needs full ingestion")
                continue

            print(f"  FIX   '{title}' — Chroma has {chunks} chunks, setting DB status READY")
            script.status          = "READY"
            script.ingestion_error = None
            script.chunks_stored   = chunks
            if not script.ingested_at:
                script.ingested_at = datetime.utcnow()
            db.commit()
            print(f"        -> Done. Status now: READY")


def phase2_reingest_true_failed():
    """Phase 2: full re-ingestion for movies with no Chroma embeddings."""
    from app.services.ingestion_service import IngestionService, IngestionError

    print("\n" + "=" * 70)
    print("PHASE 2 — Re-ingesting true-FAILED movies (no embeddings)")
    print("=" * 70)

    results = {"ok": [], "failed": []}

    for title in TRUE_FAILED:
        print(f"\n  [{title}]")

        with Session(engine) as db:
            script = db.query(MovieScript).filter(MovieScript.title == title).first()
            if not script:
                print(f"    SKIP — not found in DB")
                continue

            script_id       = script.id
            supabase_path   = script.supabase_path
            file_path       = script.file_path

        if not supabase_path and not file_path:
            print(f"    FAIL — no Supabase path and no local file_path in DB record")
            results["failed"].append((title, "No PDF source available"))
            continue

        # Mark PROCESSING before starting
        with Session(engine) as db:
            s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
            if s:
                s.status = "PROCESSING"
                db.commit()

        print(f"    Source: supabase_path='{supabase_path}' | file_path='{file_path}'")
        print(f"    Starting ingestion…")
        t0 = time.monotonic()

        try:
            svc = IngestionService()

            if supabase_path:
                chunks = svc.ingest_movie(
                    movie_name=title,
                    movie_id=script_id,
                    supabase_filename=supabase_path,
                )
            else:
                # Try local fallback — file_path may be absolute or just a filename
                from pathlib import Path
                fp = Path(file_path)
                if fp.exists():
                    local_path = fp
                else:
                    # Try relative to movie_scripts/ beside the backend
                    project_root = Path(__file__).resolve().parent.parent
                    local_path = project_root / "movie_scripts" / fp.name
                if not local_path.exists():
                    raise IngestionError(f"Local PDF not found: tried '{fp}' and '{local_path}'")
                chunks = svc.ingest_movie(
                    movie_name=title,
                    movie_id=script_id,
                    local_pdf_path=local_path,
                )

            elapsed = round(time.monotonic() - t0)
            print(f"    OK — {chunks} chunks embedded in {elapsed}s")

            # Update DB to READY
            with Session(engine) as db:
                s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
                if s:
                    s.status          = "READY"
                    s.chunks_stored   = chunks
                    s.ingested_at     = datetime.utcnow()
                    s.ingestion_error = None
                    db.commit()

            # Verify Chroma
            actual_chunks = verify_chroma(title)
            print(f"    Chroma verification: {actual_chunks} chunks retrievable")
            results["ok"].append(title)

        except Exception as exc:
            elapsed = round(time.monotonic() - t0)
            error_msg = str(exc)[:500]
            print(f"    FAIL after {elapsed}s — {error_msg}")

            with Session(engine) as db:
                s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
                if s:
                    s.status          = "FAILED"
                    s.ingestion_error = error_msg
                    db.commit()

            results["failed"].append((title, error_msg))

    return results


def final_audit():
    """Print final state of all movies after repairs."""
    col = _get_chroma_collection()
    print("\n" + "=" * 70)
    print("FINAL AUDIT — Post-repair status")
    print("=" * 70)

    with Session(engine) as db:
        movies = db.query(MovieScript).order_by(MovieScript.id).all()

    print(f"\n{'ID':<5} {'Title':<35} {'DB Status':<12} {'Chroma':<8}")
    print("-" * 65)
    for m in movies:
        try:
            r = col.get(where={"movie_name": m.title})
            c = len(r["ids"])
        except Exception:
            c = -1
        flag = "OK" if m.status == "READY" and c > 0 else ("WARN" if m.status == "READY" else "FAIL")
        print(f"{m.id:<5} {m.title:<35} {m.status:<12} {c:<8}  {flag}")


if __name__ == "__main__":
    print("FilmInsight — Movie Repair Script")
    print(f"Started at {datetime.now().strftime('%H:%M:%S')}")

    phase1_fix_stale_failed()

    results = phase2_reingest_true_failed()

    final_audit()

    print("\n" + "=" * 70)
    print("REPAIR COMPLETE")
    print(f"  Successfully repaired : {len(results['ok'])}")
    print(f"  Still failed          : {len(results['failed'])}")
    if results["failed"]:
        for t, err in results["failed"]:
            print(f"    - {t}: {err[:80]}")
    print()
