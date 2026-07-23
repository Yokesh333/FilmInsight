"""
verification_tests.py
Script to run the user's isolation tests.
"""
import os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.movie_script import MovieScript
from app.services.rag_service import _get_chroma_collection

def get_movie_vectors(movie_id: int):
    col = _get_chroma_collection()
    res = col.get(where={"movie_id": movie_id})
    return len(res.get("ids", []))

def run_tests():
    # Setup
    with Session(engine) as db:
        # Let's pick 'The Dark Knight' (ID=25) as Movie A and 'The Dark Knight Rises' (ID=24) as Movie B.
        movie_a = db.query(MovieScript).filter(MovieScript.id == 25).first()
        movie_b = db.query(MovieScript).filter(MovieScript.id == 24).first()
        
    print(f"=== INITIAL STATE ===")
    a_id, b_id = movie_a.id, movie_b.id
    a_vecs_initial = get_movie_vectors(a_id)
    b_vecs_initial = get_movie_vectors(b_id)
    
    print(f"Movie A ({movie_a.title}): ID={a_id}, Vectors={a_vecs_initial}")
    print(f"Movie B ({movie_b.title}): ID={b_id}, Vectors={b_vecs_initial}")
    
    assert a_vecs_initial > 0, "Movie A must be READY and have vectors"
    assert b_vecs_initial > 0, "Movie B must be READY and have vectors"

    # Test 1: Upload / Retry Movie B -> Movie A vectors unchanged
    print("\n=== TEST 1 & 2: Retry Movie B ===")
    from app.routers.admin import _delete_chroma_vectors, _run_ingestion_background
    from app.core.config import get_settings
    settings = get_settings()

    print(f"Triggering Admin Re-ingest for Movie B (ID={b_id})...")
    # Simulate the admin router clear step
    _delete_chroma_vectors(b_id)
    
    a_vecs_mid = get_movie_vectors(a_id)
    b_vecs_mid = get_movie_vectors(b_id)
    print(f"Mid-Reingest - Movie A Vectors: {a_vecs_mid}")
    print(f"Mid-Reingest - Movie B Vectors: {b_vecs_mid}")
    
    assert a_vecs_mid == a_vecs_initial, "Movie A vectors MUST NOT change when Movie B is deleted"
    assert b_vecs_mid == 0, "Movie B vectors must be deleted"

    print("Running IngestionService for Movie B...")
    with Session(engine) as db:
        s = db.query(MovieScript).filter(MovieScript.id == b_id).first()
        s.status = "UPLOADED"
        db.commit()

    _run_ingestion_background(b_id, settings.DATABASE_URL)
    
    a_vecs_after = get_movie_vectors(a_id)
    b_vecs_after = get_movie_vectors(b_id)
    print(f"After Reingest - Movie A Vectors: {a_vecs_after}")
    print(f"After Reingest - Movie B Vectors: {b_vecs_after}")
    
    assert a_vecs_after == a_vecs_initial, "Movie A vectors MUST NOT change after Movie B is re-ingested"
    assert b_vecs_after > 0, "Movie B must have vectors again"

    print("\n=== TEST 3: Delete Movie B ===")
    print(f"Deleting Movie B (ID={b_id}) vectors...")
    _delete_chroma_vectors(b_id)
    
    a_vecs_final = get_movie_vectors(a_id)
    b_vecs_final = get_movie_vectors(b_id)
    print(f"Final - Movie A Vectors: {a_vecs_final}")
    print(f"Final - Movie B Vectors: {b_vecs_final}")
    
    assert a_vecs_final == a_vecs_initial, "Movie A vectors MUST NOT change after Movie B is deleted"
    assert b_vecs_final == 0, "Movie B vectors must be deleted"
    
    # Restore Movie B
    print("\nRestoring Movie B...")
    _run_ingestion_background(b_id, settings.DATABASE_URL)
    print(f"Restore Complete - Movie B Vectors: {get_movie_vectors(b_id)}")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
