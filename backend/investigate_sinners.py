import sys
from app.db.database import SessionLocal
from app.models.movie_script import MovieScript
import chromadb
from chromadb.config import Settings
from app.services.rag_service import _resolve_chroma_dir, _get_chroma_collection

def main():
    print("--- 1. PostgreSQL Verification ---")
    db = SessionLocal()
    script = db.query(MovieScript).filter(MovieScript.title == "Sinners").first()
    if not script:
        print("Could not find 'Sinners' in PostgreSQL.")
        return
        
    print(f"ID: {script.id}")
    print(f"movie_name (title): '{script.title}'")
    print(f"tmdb_id: {script.tmdb_id}")
    print(f"status: {script.status}")
    print(f"file_path: {script.file_path}")
    print(f"supabase_path: {script.supabase_path}")
    print(f"uploaded_at: {script.uploaded_at}")
    print(f"ingested_at: {script.ingested_at}")

    print(f"\n--- 2. ChromaDB Verification ({_resolve_chroma_dir()}) ---")
    col = _get_chroma_collection()
    
    results = col.get()
    
    sinners_docs = []
    metadata_values = set()
    for meta, doc_id in zip(results.get("metadatas", []), results.get("ids", [])):
        if meta and "movie_name" in meta:
            m_name = meta["movie_name"]
            metadata_values.add(m_name)
            if "Sinners" in m_name:
                sinners_docs.append((doc_id, meta))
        
    print(f"Number of vectors containing 'Sinners' in metadata: {len(sinners_docs)}")
    if sinners_docs:
        print("First 3 document IDs:")
        for doc_id, meta in sinners_docs[:3]:
            print(f" - {doc_id}")
        print("First 3 metadata objects:")
        for doc_id, meta in sinners_docs[:3]:
            print(f" - {meta}")
            
    print("\n--- 3. Metadata Consistency ---")
    print(f"PostgreSQL Title: '{script.title}'")
    
    # Check for direct match
    direct_match = col.get(where={"movie_name": script.title})
    print(f"Vectors with EXACT where='{script.title}': {len(direct_match.get('ids', []))}")
    
    print("\nAll unique movie_name values in Chroma:")
    for v in sorted(metadata_values):
        print(f" - '{v}'")

if __name__ == "__main__":
    main()
