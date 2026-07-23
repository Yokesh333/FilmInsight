"""
migrate.py -- FilmInsight Database & Chroma Consistency Migration.

Run this script once (or as needed) from the backend/ directory:
    cd backend
    python migrate.py

What it does:
  1. Maps legacy status values to canonical uppercase statuses.
     uploaded   -> UPLOADED
     ingesting  -> PROCESSING   (then immediately reset to UPLOADED for re-ingestion)
     processing -> PROCESSING   (then reset to UPLOADED -- crash recovery)
     ingested   -> READY
     failed     -> FAILED

  2. Crash recovery: any PROCESSING record is reset to UPLOADED.

  3. Chroma consistency check: for every READY movie, confirm that vectors
     actually exist in Chroma with the correct movie_name metadata.
     If vectors are missing -> reset to UPLOADED so the movie will be re-ingested.

  4. Prints a full summary.
"""

from __future__ import annotations

import io
import os
import sys

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

# ── Bootstrap: make backend/ the Python root ─────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Load .env files
from dotenv import load_dotenv
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)

from app.db.database import SessionLocal
from app.models.movie_script import MovieScript

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Status mapping: any of these lowercase / legacy values → canonical uppercase
LEGACY_STATUS_MAP: dict[str, str] = {
    "uploaded":   "UPLOADED",
    "ingesting":  "UPLOADED",    # was mid-process → treat as needs re-ingestion
    "processing": "UPLOADED",    # stale PROCESSING → reset for re-ingestion
    "ingested":   "READY",
    "failed":     "FAILED",
}

# Canonical stale statuses to reset to UPLOADED (crash recovery)
STALE_PROCESSING_STATUSES = {"PROCESSING"}


# ─────────────────────────────────────────────────────────────────────────────
# Chroma helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_chroma_collection():
    """Open the Chroma collection using the same config as IngestionService."""
    try:
        import chromadb
        from chromadb.config import Settings
        from app.core.config import get_settings

        s         = get_settings()
        chroma_dir = Path(
            os.environ.get("CHROMA_DB_DIR", "")
            or getattr(s, "CHROMA_DB_DIR", "")
            or _resolve_chroma_dir()
        )
        col_name = (
            os.environ.get("CHROMA_COLLECTION_NAME", "")
            or getattr(s, "CHROMA_COLLECTION_NAME", "filminsight_scripts")
        )
        if not chroma_dir.exists():
            return None

        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        return client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:
        print(f"  [WARN] Could not open Chroma collection: {exc}")
        return None


def _resolve_chroma_dir() -> str:
    here = Path(__file__).resolve().parent
    for candidate in [here, here.parent]:
        chroma = candidate / "chroma_db"
        if chroma.exists():
            return str(chroma)
    return str(here / "chroma_db")


def _vectors_exist(col, movie_name: str) -> bool:
    """Return True if at least one vector exists for movie_name in Chroma."""
    try:
        result = col.get(where={"movie_name": movie_name}, limit=1)
        ids = result.get("ids", [])
        return bool(ids)
    except Exception as exc:
        print(f"  [WARN] Chroma query failed for '{movie_name}': {exc}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Migration runner
# ─────────────────────────────────────────────────────────────────────────────

def run_migration() -> None:
    print("=" * 62)
    print("  FilmInsight -- Database & Chroma Migration")
    print("=" * 62)

    db  = SessionLocal()
    col = _get_chroma_collection()

    if col is None:
        print("\n  [WARN] Chroma not available -- consistency check skipped.")
        chroma_available = False
    else:
        print(f"\n  Chroma: {col.count()} total vectors found.")
        chroma_available = True

    all_scripts = db.query(MovieScript).all()
    print(f"\n  PostgreSQL: {len(all_scripts)} total movie_scripts records.\n")

    # ── Phase 1: Legacy status mapping ───────────────────────────────────────
    print("-" * 62)
    print("  PHASE 1 -- Legacy Status Mapping")
    print("-" * 62)

    legacy_migrated = 0
    for s in all_scripts:
        if s.status in LEGACY_STATUS_MAP:
            old = s.status
            s.status = LEGACY_STATUS_MAP[old]
            print(f"  [MAPPED]  '{s.title}': {old!r} → {s.status!r}")
            legacy_migrated += 1

    if legacy_migrated:
        db.commit()
    print(f"\n  Mapped {legacy_migrated} legacy status value(s).\n")

    # ── Phase 2: Crash recovery — reset stale PROCESSING ─────────────────────
    print("-" * 62)
    print("  PHASE 2 -- Crash Recovery (Stale PROCESSING -> UPLOADED)")
    print("-" * 62)

    stale_reset = 0
    # Reload after phase 1 commit
    all_scripts = db.query(MovieScript).all()
    for s in all_scripts:
        if s.status in STALE_PROCESSING_STATUSES:
            print(f"  [RESET]   '{s.title}': PROCESSING → UPLOADED (crash recovery)")
            s.status          = "UPLOADED"
            s.ingestion_error = "Reset by migration: was stuck in PROCESSING"
            stale_reset += 1

    if stale_reset:
        db.commit()
    print(f"\n  Reset {stale_reset} stale PROCESSING record(s).\n")

    # ── Phase 3: Chroma consistency check ─────────────────────────────────────
    print("-" * 62)
    print("  PHASE 3 -- Chroma Consistency Check (READY movies)")
    print("-" * 62)

    if not chroma_available:
        print("  [SKIP] Chroma not available -- skipping consistency check.\n")
        chroma_inconsistent = 0
    else:
        chroma_inconsistent = 0
        all_scripts = db.query(MovieScript).all()
        for s in all_scripts:
            if s.status != "READY":
                continue
            exists = _vectors_exist(col, s.title)
            if exists:
                print(f"  [OK]      '{s.title}': vectors present in Chroma")
            else:
                print(f"  [MISSING] '{s.title}': READY in DB but 0 vectors in Chroma -> resetting to UPLOADED")
                s.status          = "UPLOADED"
                s.ingestion_error = "Reset by migration: no vectors found in Chroma"
                chroma_inconsistent += 1

        if chroma_inconsistent:
            db.commit()
        print(f"\n  Found {chroma_inconsistent} READY movie(s) with missing Chroma vectors (reset to UPLOADED).\n")

    db.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 62)
    print("  MIGRATION SUMMARY")
    print("=" * 62)
    print(f"  Legacy statuses mapped  : {legacy_migrated}")
    print(f"  Stale PROCESSING reset  : {stale_reset}")
    print(f"  Chroma inconsistencies  : {chroma_inconsistent if chroma_available else 'skipped'}")
    print()
    print("  [DONE] Migration complete.")
    print()
    print("  Next steps:")
    print("  - If any movies were reset to UPLOADED, run the ingestion pipeline:")
    print("    POST /api/admin/ingest   (via Admin Dashboard -> Ingestion Engine)")
    print("    OR restart the backend to trigger startup ingestion.")
    print("=" * 62)


if __name__ == "__main__":
    run_migration()
