import asyncio
import time
import httpx
import logging
from sqlalchemy import create_engine
from statistics import mean

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:YokeshYoki333*@db.vbymfkwiotcrncqccbyl.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

def get_active_connections():
    try:
        with engine.connect() as conn:
            res = conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = 'postgres' AND state = 'active'").scalar()
        return res
    except Exception:
        return -1

async def make_request(client, method, url, name, metrics, **kwargs):
    start = time.time()
    try:
        if method == "GET":
            r = await client.get(url, **kwargs)
        else:
            r = await client.post(url, **kwargs)
        elapsed = time.time() - start
        metrics[name].append(elapsed)
        logger.info(f"{name} completed in {elapsed:.2f}s (Status: {r.status_code})")
    except Exception as e:
        logger.error(f"{name} failed after {time.time() - start:.2f}s: {e}")

async def run_test():
    url_base = "http://127.0.0.1:8000"
    metrics = {"chat": [], "homepage": [], "login": []}
    
    logger.info("Starting Concurrency Test...")
    logger.info(f"Initial DB Active Connections: {get_active_connections()}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Launch 5 concurrent chats
        tasks = []
        for i in range(5):
            tasks.append(asyncio.create_task(
                make_request(client, "POST", f"{url_base}/chat", "chat", metrics, json={
                    "question": f"What happens to character {i}?",
                    "sessionId": "test-session",
                    "movie_name": "Inception"
                })
            ))
            
        # Wait 2 seconds, then hit homepage 10 times concurrently
        await asyncio.sleep(2)
        logger.info(f"Mid-chat DB Active Connections: {get_active_connections()}")
        
        for i in range(10):
            tasks.append(asyncio.create_task(
                make_request(client, "GET", f"{url_base}/movie/our-movies", "homepage", metrics)
            ))
            
        # Hit login 5 times
        for i in range(5):
            tasks.append(asyncio.create_task(
                make_request(client, "POST", f"{url_base}/api/auth/login", "login", metrics, data={
                    "username": "admin@filminsight.com",
                    "password": "password"
                })
            ))
            
        await asyncio.gather(*tasks)
        
    logger.info(f"Final DB Active Connections: {get_active_connections()}")
    
    logger.info("--- METRICS ---")
    for k, v in metrics.items():
        if v:
            logger.info(f"{k.upper()}: {len(v)} requests, Avg = {mean(v):.2f}s, Max = {max(v):.2f}s")
        else:
            logger.info(f"{k.upper()}: 0 requests completed")

if __name__ == "__main__":
    asyncio.run(run_test())
