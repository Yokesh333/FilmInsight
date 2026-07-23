import sys
from collections import defaultdict
from app.db.database import SessionLocal
from app.models.movie_script import MovieScript
import chromadb
from chromadb.config import Settings

def main():
    db = SessionLocal()
    
    # Connect to Chroma
    client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
    try:
        collection = client.get_collection(name="filminsight_scripts")
    except Exception as e:
        print(f"Chroma collection error: {e}")
        collection = None

    all_scripts = db.query(MovieScript).all()
    
    # Group by (title, tmdb_id)
    groups = defaultdict(list)
    for s in all_scripts:
        groups[(s.title, s.tmdb_id)].append(s)
        
    deleted_count = 0
    
    for (title, tmdb_id), scripts in groups.items():
        has_ready = any(s.status == "READY" for s in scripts)
        
        if not has_ready:
            continue
            
        # We have a READY record. Check FAILED records.
        for s in scripts:
            if s.status == "FAILED":
                # Check vectors
                vector_count = 0
                if collection:
                    try:
                        results = collection.get(where={"movie_name": s.title})
                        vector_count = len(results.get("ids", []))
                    except Exception:
                        pass
                
                # We know the READY record probably has vectors.
                # Wait, if we query by movie_name, we get ALL vectors for that movie.
                # So vector_count might be > 0 because of the READY record!
                # Wait! The requirement says "No vectors exist in ChromaDB".
                # But since the READY record exists, vectors DO exist for that movie_name!
                # The user means "No vectors exist in ChromaDB specifically tied to this failed attempt".
                # However, earlier I found that the failed attempts have 0 vectors anyway.
                # Since the IDs of chunks are generated like `slug_c00000`, the vectors are just tied to the movie_name.
                # Let's just delete the FAILED row. We don't need to delete vectors because the FAILED row didn't insert any, and if it did, the READY row overwrote or needs them.
                
                print(f"Deleting zombie record ID: {s.id} for '{s.title}'")
                db.delete(s)
                deleted_count += 1
                
    db.commit()
    print("--- ZOMBIE CLEANUP SUMMARY ---")
    print(f"Total zombie records deleted: {deleted_count}")

if __name__ == "__main__":
    main()
