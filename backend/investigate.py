import sys
from collections import defaultdict
from app.db.database import SessionLocal
from app.models.movie_script import MovieScript
import chromadb
from chromadb.config import Settings

def main():
    print("--- 1. QUERYING FAILED MOVIES ---")
    db = SessionLocal()
    failed_scripts = db.query(MovieScript).filter(MovieScript.status == "FAILED").all()
    
    for s in failed_scripts:
        print(f"Movie: {s.title}")
        print(f"Status: {s.status}")
        print(f"Ingestion Error: {s.ingestion_error}")
        print(f"Uploaded At: {s.uploaded_at}")
        print(f"Ingested At: {s.ingested_at}")
        print("-" * 40)
        
    print("\n--- 2. & 3. QUERYING CHROMA DB AND DETERMINING REASON ---")
    client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
    
    try:
        collection = client.get_collection(name="filminsight_scripts")
    except Exception as e:
        print(f"Could not load chroma collection: {e}")
        collection = None
        
    summary_data = []
        
    for s in failed_scripts:
        vector_count = 0
        if collection:
            try:
                results = collection.get(where={"movie_name": s.title})
                vector_count = len(results.get("ids", []))
            except Exception as e:
                print(f"Error querying chroma for {s.title}: {e}")
                
        reason = "Unknown"
        err = s.ingestion_error or ""
        
        if "out of memory" in err.lower() or "oom" in err.lower() or "killed" in err.lower() or "memoryerror" in err.lower():
            reason = "Embedding crashed (OOM)"
        elif "pymupdf" in err.lower() or "extractable text" in err.lower():
            reason = "PDF extraction failed"
        elif "chroma" in err.lower() or "upsert" in err.lower():
            reason = "Chroma insertion failed"
        elif not err:
            reason = "Unknown"
        else:
            reason = "Unknown"
            
        if vector_count > 0:
            reason = "Partial embeddings exist"
            
        if not err and vector_count == 0:
            reason = "Embedding never started"
            
        summary_data.append((s.title, s.status, vector_count, reason))
        
    print("\n--- 4. SUMMARY TABLE ---")
    print(f"{'Movie':<30} | {'Status':<10} | {'Chroma Vectors':<15} | {'Failure Reason'}")
    print("-" * 90)
    for row in summary_data:
        print(f"{row[0]:<30} | {row[1]:<10} | {row[2]:<15} | {row[3]}")
        
    print("\n--- DUPLICATE MOVIES ---")
    all_scripts = db.query(MovieScript).all()
    duplicates_map = defaultdict(list)
    
    for s in all_scripts:
        key = (s.title, s.tmdb_id)
        duplicates_map[key].append(s)
        
    for key, scripts in duplicates_map.items():
        if len(scripts) > 1:
            print(f"\nDuplicates for: {key[0]} (TMDB ID: {key[1]})")
            for s in scripts:
                print(f"ID: {s.id} | Status: {s.status} | Uploaded At: {s.uploaded_at}")

if __name__ == "__main__":
    main()
