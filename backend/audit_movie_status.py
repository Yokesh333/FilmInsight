"""
audit_movie_status.py
─────────────────────
Verifies the status of every MovieScript row in PostgreSQL against
what is actually stored in Chroma.

Prints a table:
  title | DB status | Chroma chunks | Verdict
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.rag_service import _get_chroma_collection

def audit():
    col = _get_chroma_collection()
    chroma_total = col.count()
    print(f"\nChroma total documents in collection: {chroma_total}\n")

    with Session(engine) as db:
        movies = db.query(MovieScript).order_by(MovieScript.id).all()

    print(f"{'ID':<5} {'Title':<35} {'DB Status':<12} {'Chroma Chunks':<15} {'Verdict'}")
    print("-" * 90)

    ready_ok      = []
    failed_no_emb = []
    ready_no_emb  = []
    failed_has_emb = []

    for m in movies:
        try:
            results = col.get(where={"movie_name": m.title})
            chunk_count = len(results["ids"])
        except Exception as e:
            chunk_count = -1

        status = m.status or "NULL"

        if status == "READY" and chunk_count > 0:
            verdict = "OK READY + embedded"
            ready_ok.append(m.title)
        elif status == "READY" and chunk_count == 0:
            verdict = "WARN READY in DB but NO Chroma embeddings!"
            ready_no_emb.append(m.title)
        elif status == "FAILED" and chunk_count > 0:
            verdict = "WARN FAILED in DB but HAS embeddings (stale FAILED?)"
            failed_has_emb.append(m.title)
        elif status == "FAILED" and chunk_count == 0:
            verdict = "FAIL needs re-ingestion"
            failed_no_emb.append(m.title)
        elif status in ("UPLOADED", "PROCESSING"):
            verdict = f"PENDING Still {status}"
        else:
            verdict = f"UNKNOWN ({status})"

        print(f"{m.id:<5} {m.title:<35} {status:<12} {chunk_count:<15} {verdict}")

    print("\n" + "=" * 90)
    print(f"SUMMARY")
    print(f"  READY + properly embedded    : {len(ready_ok)}")
    print(f"  FAILED + no embeddings       : {len(failed_no_emb)}")
    print(f"  READY but missing embeddings : {len(ready_no_emb)}")
    print(f"  FAILED but has embeddings    : {len(failed_has_emb)}")

    if ready_no_emb:
        print(f"\n  CRITICAL - READY in DB but have NO screenplay chunks:")
        for t in ready_no_emb:
            print(f"      - {t}")

    if failed_has_emb:
        print(f"\n  FAILED in DB but DO have Chroma embeddings (status may be stale):")
        for t in failed_has_emb:
            print(f"      - {t}")

    if failed_no_emb:
        print(f"\n  Movies that need re-ingestion:")
        for t in failed_no_emb:
            print(f"      - {t}")

    print()

if __name__ == "__main__":
    audit()
