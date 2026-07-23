import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.rag_service import _get_chroma_collection

def check_chroma():
    col = _get_chroma_collection()
    
    # Check total chunks for Sinners
    results = col.get(
        where={"movie_title": "Sinners"}
    )
    
    print(f"Number of Sinners chunks (using movie_title='Sinners'): {len(results['ids'])}")
    if len(results['ids']) > 0:
        print("Sample metadata:")
        print(results['metadatas'][0])
    
    # Try just fetching some chunks containing "Sinners" in text
    all_chunks = col.peek(limit=5)
    print("\nPeek sample metadata from collection:")
    for meta in all_chunks['metadatas']:
        print(meta)

if __name__ == "__main__":
    check_chroma()
