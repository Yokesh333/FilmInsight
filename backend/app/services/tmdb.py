import httpx
import logging
import re
from typing import Optional, Dict, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE_URL = settings.TMDB_BASE_URL
TMDB_IMG_BASE = settings.TMDB_IMG_BASE

OMDB_API_KEY = settings.OMDB_API_KEY or "72bf0fb9"
OMDB_BASE_URL = settings.OMDB_BASE_URL or "http://www.omdbapi.com"

async def fetch_movie_metadata(title: str, release_year: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches TMDB for a movie by title (and optionally year).
    Returns a dictionary with poster, backdrop, overview, genres, release_date, runtime, rating.
    """
    if not TMDB_API_KEY:
        logger.warning("TMDB API key is missing. Skipping metadata extraction.")
        return {}
        
    # Clean up the title a bit (e.g., remove .pdf, _script, etc if present)
    clean_title = re.sub(r'(?i)(\.pdf|_script|script|\.txt)$', '', title).strip()
    clean_title = clean_title.replace('_', ' ').replace('-', ' ')
    
    metadata = {}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Search for the movie
            search_url = f"{TMDB_BASE_URL}/search/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "query": clean_title,
                "include_adult": "false"
            }
            if release_year:
                params["primary_release_year"] = release_year
                
            resp = await client.get(search_url, params=params, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("results", [])
            if not results:
                # If we searched with year and failed, try without year
                if release_year:
                    params.pop("primary_release_year")
                    resp = await client.get(search_url, params=params, timeout=5.0)
                    resp.raise_for_status()
                    results = resp.json().get("results", [])
                    
            if not results:
                logger.info(f"No TMDB results found for title: {clean_title}")
                return {}
                
            # Take the first result
            first_match = results[0]
            tmdb_id = first_match.get("id")
            
            # 2. Get full details to extract runtime and formatted genres
            details_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
            params = {"api_key": TMDB_API_KEY}
            detail_resp = await client.get(details_url, params=params, timeout=5.0)
            detail_resp.raise_for_status()
            details = detail_resp.json()
            
            # Parse fields
            metadata["tmdb_id"] = tmdb_id
            
            poster_path = details.get("poster_path")
            if poster_path:
                metadata["poster_url"] = f"{TMDB_IMG_BASE}{poster_path}"
                
            backdrop_path = details.get("backdrop_path")
            if backdrop_path:
                metadata["backdrop_url"] = f"{TMDB_IMG_BASE}{backdrop_path}"
                
            metadata["overview"] = details.get("overview")
            metadata["release_date"] = details.get("release_date")
            metadata["runtime"] = details.get("runtime")
            metadata["rating"] = details.get("vote_average")
            
            # Formatted genres (comma-separated string)
            genres = details.get("genres", [])
            if genres:
                metadata["genres"] = ", ".join([g.get("name") for g in genres])
                
            return metadata
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"TMDB API request failed: {repr(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in TMDB extraction: {repr(e)}")
            
        # Fallback to OMDb
        if OMDB_API_KEY:
            logger.info(f"Falling back to OMDb for {clean_title}...")
            try:
                params = {"apikey": OMDB_API_KEY, "t": clean_title}
                if release_year:
                    params["y"] = release_year
                resp = await client.get(OMDB_BASE_URL, params=params, timeout=5.0)
                resp.raise_for_status()
                omdb = resp.json()
                if omdb.get("Response") == "True":
                    metadata["tmdb_id"] = None
                    poster = omdb.get("Poster")
                    if poster and poster != "N/A":
                        metadata["poster_url"] = poster
                    metadata["backdrop_url"] = None
                    metadata["overview"] = omdb.get("Plot")
                    metadata["release_date"] = omdb.get("Released")
                    
                    try:
                        rating = float(omdb.get("imdbRating", 0)) if omdb.get("imdbRating", "N/A") != "N/A" else 0.0
                    except:
                        rating = 0.0
                    metadata["rating"] = rating
                    metadata["genres"] = omdb.get("Genre")
                    
                    # Parse runtime "148 min" -> 148
                    runtime_str = omdb.get("Runtime", "")
                    try:
                        metadata["runtime"] = int(runtime_str.split()[0])
                    except:
                        metadata["runtime"] = None
                        
                    return metadata
            except Exception as ex:
                logger.error(f"OMDb fallback failed: {repr(ex)}")
                
        return {}

async def fetch_movie_metadata_by_id(tmdb_id: int) -> Dict[str, Any]:
    """
    Fetches exact movie metadata and credits from TMDB by its TMDB ID.
    """
    if not TMDB_API_KEY:
        logger.warning("TMDB API key is missing. Skipping metadata extraction.")
        return {}

    metadata = {}
    async with httpx.AsyncClient() as client:
        try:
            # 1. Get full details
            details_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
            params = {"api_key": TMDB_API_KEY}
            detail_resp = await client.get(details_url, params=params, timeout=5.0)
            detail_resp.raise_for_status()
            details = detail_resp.json()

            # 2. Get credits
            credits_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
            credits_resp = await client.get(credits_url, params=params, timeout=5.0)
            credits = credits_resp.json() if credits_resp.status_code == 200 else {}

            metadata["tmdb_id"] = tmdb_id
            metadata["title"] = details.get("title")
            metadata["original_title"] = details.get("original_title")
            
            poster_path = details.get("poster_path")
            if poster_path:
                metadata["poster_url"] = f"{TMDB_IMG_BASE}{poster_path}"
                
            backdrop_path = details.get("backdrop_path")
            if backdrop_path:
                metadata["backdrop_url"] = f"{TMDB_IMG_BASE}{backdrop_path}"
                
            metadata["overview"] = details.get("overview")
            metadata["release_date"] = details.get("release_date")
            metadata["runtime"] = details.get("runtime")
            metadata["rating"] = details.get("vote_average")
            metadata["vote_count"] = details.get("vote_count")
            metadata["popularity"] = details.get("popularity")
            metadata["original_language"] = details.get("original_language")
            
            # Formatted genres (comma-separated string)
            genres = details.get("genres", [])
            if genres:
                metadata["genres"] = ", ".join([g.get("name") for g in genres])
                
            # Parse director
            crew = credits.get("crew", [])
            directors = [member["name"] for member in crew if member.get("job") == "Director"]
            if directors:
                metadata["director"] = ", ".join(directors)
                
            # Parse main cast
            cast = credits.get("cast", [])
            main_cast = [member["name"] for member in cast[:8]]
            if main_cast:
                metadata["cast"] = ", ".join(main_cast)
                
            return metadata
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"TMDB API request failed: {repr(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in TMDB extraction by id: {repr(e)}")
            
        return {}
