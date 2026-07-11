"""
movie.py — Movie metadata router for FilmInsight.

Fetches live data from TMDb and OMDb APIs:
  • Posters, backdrops, overview
  • IMDb rating, genre, runtime, director, cast
  • Quotes (from OMDb / curated set)
  • Trivia facts
  • /movie/details   — full rich metadata
  • /movie/popular   — list of popular movies with posters
  • /movie           — basic lookup (legacy)
  • /movie/list      — list known titles
"""

import logging
import httpx
from fastapi import APIRouter, Query, HTTPException
from app.core.config import get_settings
from app.models.schemas import MovieResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/movie', tags=['Movie'])

# ── API config ────────────────────────────────────────────────────────────────
TMDB_BASE   = "https://api.themoviedb.org/3"
TMDB_IMG    = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_HD = "https://image.tmdb.org/t/p/original"
OMDB_BASE   = "http://www.omdbapi.com/"
TIMEOUT     = httpx.Timeout(12.0)

# ── Curated trivia & quotes per movie (supplement API data) ──────────────────
MOVIE_EXTRAS = {
    "inception": {
        "trivia": [
            "The film took Christopher Nolan 10 years to write.",
            "The spinning top at the end was Cobb's dead wife's totem — not his own.",
            "Hans Zimmer slowed Édith Piaf's 'Non, je ne regrette rien' to create the score.",
            "The hallway fight scene required a set built on a rotating gimbal.",
            "Joseph Gordon-Levitt trained for months for the zero-gravity corridor fight.",
        ],
        "quotes": [
            {"text": "You mustn't be afraid to dream a little bigger, darling.", "speaker": "Eames"},
            {"text": "An idea is like a virus, resilient, highly contagious.", "speaker": "Cobb"},
            {"text": "What is the most resilient parasite? An idea.", "speaker": "Cobb"},
            {"text": "I can't imagine you with a totem.", "speaker": "Ariadne"},
            {"text": "Inception. Is it possible?", "speaker": "Saito"},
        ],
    },
    "interstellar": {
        "trivia": [
            "Matthew McConaughey's tears in the film were genuine; the scene took one take.",
            "NASA scientists consulted on the film to ensure scientific accuracy.",
            "The wormhole and black hole visuals were created with new astrophysics software.",
            "Hans Zimmer recorded the score before seeing the finished film.",
            "The cornfield used 500 acres of real corn grown for the production.",
        ],
        "quotes": [
            {"text": "We used to look up at the sky and wonder at our place in the stars.", "speaker": "Cooper"},
            {"text": "Do not go gentle into that good night.", "speaker": "Brand"},
            {"text": "Love is the one thing we're capable of perceiving that transcends time.", "speaker": "Brand"},
            {"text": "Mankind was born on Earth. It was never meant to die here.", "speaker": "Cooper"},
            {"text": "We've always defined ourselves by the ability to overcome the impossible.", "speaker": "Cooper"},
        ],
    },
    "500 days of summer": {
        "trivia": [
            "The film is not a love story, according to the opening title card.",
            "Zooey Deschanel's natural hair color influenced Summer's character design.",
            "The IKEA scene was partly improvised by the two leads.",
            "The non-linear structure was inspired by Annie Hall.",
            "Joseph Gordon-Levitt has said Tom is not the hero of the story.",
        ],
        "quotes": [
            {"text": "I'm not easy to understand, Tom. And you can't figure me out by watching me walk.", "speaker": "Summer"},
            {"text": "Most days of the year are unremarkable.", "speaker": "Narrator"},
            {"text": "I love how she makes me feel, like anything's possible.", "speaker": "Tom"},
            {"text": "I just... I just woke up one day and I knew.", "speaker": "Summer"},
            {"text": "You know what's weird? I don't feel that bad.", "speaker": "Tom"},
        ],
    },
    "the dark knight": {
        "trivia": [
            "Heath Ledger stayed in a hotel room for six weeks to develop the Joker's character.",
            "The Joker's 'magic trick' pencil scene was not in the original script.",
            "The film was the first Batman movie to not have 'Batman' in the title.",
            "Christopher Nolan used real IMAX cameras for 28 minutes of footage.",
            "Heath Ledger kept a 'Joker diary' documenting the character's psychology.",
        ],
        "quotes": [
            {"text": "Why so serious?", "speaker": "The Joker"},
            {"text": "Some men just want to watch the world burn.", "speaker": "Alfred"},
            {"text": "You either die a hero, or you live long enough to see yourself become the villain.", "speaker": "Harvey Dent"},
            {"text": "This city deserves a better class of criminal.", "speaker": "The Joker"},
            {"text": "I believe whatever doesn't kill you simply makes you... stranger.", "speaker": "The Joker"},
        ],
    },
    "memento": {
        "trivia": [
            "Christopher Nolan wrote the screenplay while working as a bank teller.",
            "The film was shot chronologically, but edited in reverse for the audience.",
            "Guy Pearce wore contact lenses to play a character with short-term memory loss.",
        ],
        "quotes": [
            {"text": "Memory can change the shape of a room.", "speaker": "Leonard"},
            {"text": "I have to believe that my actions still have meaning.", "speaker": "Leonard"},
            {"text": "How am I supposed to heal if I can't feel time?", "speaker": "Leonard"},
        ],
    },
    "tenet": {
        "trivia": [
            "Christopher Nolan shot the film in 70mm for maximum visual impact.",
            "The inverted action sequences required actors to learn moves backwards.",
            "The word 'Tenet' is a palindrome — it reads the same forwards and backwards.",
        ],
        "quotes": [
            {"text": "Don't try to understand it. Feel it.", "speaker": "Protagonist"},
            {"text": "What's happened, happened.", "speaker": "Neil"},
            {"text": "You have a future in the past.", "speaker": "Ives"},
        ],
    },
    "openheimer": {
        "trivia": [
            "Cillian Murphy lost considerable weight to portray Oppenheimer.",
            "The Trinity test was recreated practically without CGI.",
            "Christopher Nolan refused to use CGI for the nuclear explosion.",
        ],
        "quotes": [
            {"text": "Now I am become Death, the destroyer of worlds.", "speaker": "Oppenheimer"},
            {"text": "We imagined we might make a thing that would end all wars.", "speaker": "Oppenheimer"},
            {"text": "Theory will only take you so far.", "speaker": "Oppenheimer"},
        ],
    },
}


def _get_extras(title: str) -> dict:
    """Return curated trivia and quotes for a movie title."""
    key = title.lower().strip()
    for k, v in MOVIE_EXTRAS.items():
        if k in key or key in k:
            return v
    return {"trivia": [], "quotes": []}


# ── TMDb helpers ──────────────────────────────────────────────────────────────

async def _tmdb_search(title: str, api_key: str) -> dict | None:
    """Search TMDb for a movie by title and return the best match."""
    url = f"{TMDB_BASE}/search/movie"
    params = {"api_key": api_key, "query": title, "language": "en-US", "page": 1}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            title_lower = title.lower()
            for item in results:
                if item.get("title", "").lower() == title_lower:
                    return item
            return results[0]
    except Exception as e:
        logger.warning(f"[TMDb] search failed for '{title}': {e}")
        return None


async def _tmdb_details(tmdb_id: int, api_key: str) -> dict:
    """Fetch full movie details from TMDb (genres, runtime, imdb_id)."""
    url = f"{TMDB_BASE}/movie/{tmdb_id}"
    params = {"api_key": api_key, "language": "en-US"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"[TMDb] details failed id={tmdb_id}: {e}")
        return {}


async def _tmdb_credits(tmdb_id: int, api_key: str) -> dict:
    """Fetch cast and crew from TMDb."""
    url = f"{TMDB_BASE}/movie/{tmdb_id}/credits"
    params = {"api_key": api_key}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"[TMDb] credits failed id={tmdb_id}: {e}")
        return {}


async def _tmdb_popular(api_key: str, page: int = 1) -> list:
    """Fetch popular movies list from TMDb."""
    url = f"{TMDB_BASE}/movie/popular"
    params = {"api_key": api_key, "language": "en-US", "page": page}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"[TMDb] popular failed: {e}")
        return []


async def _omdb_fetch(title: str, year: str | None, imdb_id: str | None, api_key: str) -> dict:
    """Fetch data from OMDb — prefers IMDb ID lookup."""
    params: dict = {"apikey": api_key}
    if imdb_id and imdb_id != "N/A":
        params["i"] = imdb_id
    else:
        params["t"] = title
        if year:
            params["y"] = year
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(OMDB_BASE, params=params)
            r.raise_for_status()
            data = r.json()
            return data if data.get("Response") == "True" else {}
    except Exception as e:
        logger.warning(f"[OMDb] fetch failed for '{title}': {e}")
        return {}


# ── Core function: build full movie data ─────────────────────────────────────

async def _build_movie_data(title: str) -> dict:
    """Fetch and merge TMDb + OMDb data for a movie title."""
    settings = get_settings()
    tmdb_key = settings.TMDB_API_KEY or "239967a7888fc811609db5aa3b554431"
    omdb_key = settings.OMDB_API_KEY or "72bf0fb9"

    # Step 1 – TMDb search
    result = await _tmdb_search(title, tmdb_key)
    if not result:
        return {
            "title": title, "year": None, "genre": [], "director": None,
            "cast": [], "plot": None, "rating": None, "runtime": None,
            "awards": None, "poster": None, "backdrop": None,
            "overview": None, "trivia": [], "quotes": [],
            "imdb_id": None, "tmdb_id": None, "tagline": None,
        }

    tmdb_id = result.get("id")

    # Step 2 – TMDb details + credits (parallel)
    details, credits = await asyncio.gather(
        _tmdb_details(tmdb_id, tmdb_key),
        _tmdb_credits(tmdb_id, tmdb_key),
    )

    # Step 3 – Extract TMDb fields
    poster_path   = result.get("poster_path") or details.get("poster_path")
    backdrop_path = result.get("backdrop_path") or details.get("backdrop_path")
    poster   = f"{TMDB_IMG}{poster_path}"     if poster_path   else None
    backdrop = f"{TMDB_IMG_HD}{backdrop_path}" if backdrop_path else None

    release_date = result.get("release_date", "")
    year  = release_date[:4] if release_date else None
    imdb_id = details.get("imdb_id")
    tagline = details.get("tagline") or ""

    genres_list = [g["name"] for g in details.get("genres", [])]

    runtime_min = details.get("runtime")
    runtime_str = f"{runtime_min} min" if runtime_min else None

    cast_list = [c["name"] for c in credits.get("cast", [])[:8]]
    directors = [c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"]
    director  = ", ".join(directors) if directors else None

    overview = result.get("overview") or details.get("overview") or ""

    # Step 4 – OMDb enrich
    omdb = await _omdb_fetch(title, year, imdb_id, omdb_key)
    imdb_rating = omdb.get("imdbRating") or str(result.get("vote_average", ""))
    awards      = omdb.get("Awards") or ""
    if not runtime_str:
        runtime_str = omdb.get("Runtime")

    try:
        rating_float = float(imdb_rating) if imdb_rating and imdb_rating != "N/A" else None
    except ValueError:
        rating_float = None

    # Step 5 – Curated extras
    extras = _get_extras(title)

    return {
        "title":    result.get("title", title),
        "year":     int(year) if year else None,
        "genre":    genres_list or (omdb.get("Genre", "").split(", ") if omdb.get("Genre") else []),
        "director": director or omdb.get("Director"),
        "cast":     cast_list or (omdb.get("Actors", "").split(", ") if omdb.get("Actors") else []),
        "plot":     overview or omdb.get("Plot"),
        "rating":   rating_float,
        "runtime":  runtime_str or omdb.get("Runtime"),
        "awards":   awards if awards != "N/A" else None,
        "poster":   poster,
        "backdrop": backdrop,
        "overview": overview,
        "tagline":  tagline,
        "imdb_id":  imdb_id,
        "tmdb_id":  tmdb_id,
        "trivia":   extras.get("trivia", []),
        "quotes":   extras.get("quotes", []),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

import asyncio


@router.get('/details', tags=['Movie'])
async def get_movie_details(title: str = Query(..., min_length=1)):
    """
    Full movie metadata: poster, backdrop, rating, cast, director,
    genre, runtime, awards, trivia, quotes — sourced from TMDb + OMDb.
    """
    logger.info(f"[/movie/details] title='{title}'")
    data = await _build_movie_data(title)
    return data


@router.get('/popular', tags=['Movie'])
async def get_popular_movies(page: int = 1):
    """
    Returns popular movies from TMDb with poster URLs, ratings, genres.
    Used by the Home page movie grid.
    """
    settings = get_settings()
    tmdb_key = settings.TMDB_API_KEY or "239967a7888fc811609db5aa3b554431"

    results = await _tmdb_popular(tmdb_key, page)

    movies = []
    for m in results[:16]:
        poster_path   = m.get("poster_path")
        backdrop_path = m.get("backdrop_path")
        genres_raw = m.get("genre_ids", [])
        release    = m.get("release_date", "")
        movies.append({
            "id":       m.get("id"),
            "title":    m.get("title"),
            "overview": m.get("overview"),
            "year":     release[:4] if release else None,
            "rating":   round(m.get("vote_average", 0), 1),
            "poster":   f"{TMDB_IMG}{poster_path}"     if poster_path   else None,
            "backdrop": f"{TMDB_IMG_HD}{backdrop_path}" if backdrop_path else None,
        })

    return {"movies": movies, "total": len(movies)}


@router.get('', response_model=MovieResponse)
async def get_movie(title: str):
    """Basic movie lookup (legacy endpoint — prefer /movie/details)."""
    data = await _build_movie_data(title)
    return MovieResponse(
        title    = data["title"],
        year     = data["year"],
        genre    = data["genre"],
        director = data["director"],
        cast     = data["cast"],
        plot     = data["plot"],
        rating   = data["rating"],
        runtime  = data["runtime"],
        awards   = data["awards"],
        poster   = data["poster"],
    )


@router.get('/list', tags=['Movie'])
async def list_movies():
    """List movie titles available in the curated extras set."""
    titles = list(MOVIE_EXTRAS.keys())
    return {"movies": [t.title() for t in titles], "total": len(titles)}
