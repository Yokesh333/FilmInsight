import asyncio
import logging
from app.services.rag_service import get_rag_service

logging.basicConfig(level=logging.INFO)

async def main():
    rag = get_rag_service()
    
    try:
        res = await rag.query(
            question="What is the plot?",
            session_id="test-123",
            movie_name="Sinners"
        )
        print("SUCCESS:")
        print(res["answer"])
    except Exception as e:
        import traceback
        print("EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
