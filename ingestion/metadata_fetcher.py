"""
metadata_fetcher.py — Movie metadata retrieval for the FilmInsight ingestion pipeline.

Fetches rich metadata from two sources:
  • TMDb  — title, overview, genres, cast, director, poster, release year
  • OMDb  — IMDb rating, runtime (as fallback / supplement)

Both are merged into a single flat :class:`MovieMetadata` object that maps
directly to the Chroma chunk metadata schema.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests

from ingestion import config
from ingestion.utils import get_logger, safe_str

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data container
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MovieMetadata:
    """
    Merged metadata for a single movie.

    All fields default to ``"N/A"`` so downstream code never encounters
    ``None`` in Chroma metadata (Chroma requires scalar values).
    """
    movie: str = "N/A"
    year: str = "N/A"
    genre: str = "N/A"
    director: str = "N/A"
    actors: str = "N/A"
    runtime: str = "N/A"
    imdb_rating: str = "N/A"
    poster: str = "N/A"
    overview: str = "N/A"
    # Internal IDs — not stored in Chroma but useful for debugging
    tmdb_id: int = -1
    imdb_id: str = "N/A"

    def to_chroma_metadata(self) -> dict[str, Any]:
        """Return only the fields required by the Chroma schema."""
        return {
            "movie": self.movie,
            "year": self.year,
            "genre": self.genre,
            "director": self.director,
            "actors": self.actors,
            "runtime": self.runtime,
            "imdb_rating": self.imdb_rating,
            "poster": self.poster,
            "overview": self.overview,
            "source": "screenplay",
        }


# ─────────────────────────────────────────────────────────────────────────────
# TMDb client
# ─────────────────────────────────────────────────────────────────────────────

class TMDbClient:
    """
    Thin wrapper around the TMDb REST API.

    Parameters
    ----------
    api_key : str
        TMDb v3 API key.
    timeout : int
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str = config.TMDB_API_KEY,
        timeout: int = config.HTTP_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    # ── Public API ────────────────────────────────────────────────────────────

    def search(self, title: str) -> dict[str, Any] | None:
        """
        Search for a movie by *title* and return the best-matching result
        dict from TMDb, or ``None`` if nothing is found.
        """
        url = f"{config.TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": self._api_key,
            "query": title,
            "language": "en-US",
            "page": 1,
        }
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                logger.warning(f"  TMDb: No results for '{title}'")
                return None
            # Pick the result whose title most closely matches
            return _best_match(title, results, key="title")
        except requests.RequestException as exc:
            logger.warning(f"  TMDb search failed for '{title}': {exc}")
            return None

    def get_credits(self, tmdb_id: int) -> dict[str, Any]:
        """Fetch cast and crew for *tmdb_id*."""
        url = f"{config.TMDB_BASE_URL}/movie/{tmdb_id}/credits"
        try:
            resp = self._session.get(
                url,
                params={"api_key": self._api_key},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.warning(f"  TMDb credits failed (id={tmdb_id}): {exc}")
            return {}

    def get_details(self, tmdb_id: int) -> dict[str, Any]:
        """Fetch full movie details including genres for *tmdb_id*."""
        url = f"{config.TMDB_BASE_URL}/movie/{tmdb_id}"
        try:
            resp = self._session.get(
                url,
                params={"api_key": self._api_key, "language": "en-US"},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.warning(f"  TMDb details failed (id={tmdb_id}): {exc}")
            return {}

    def build_metadata(self, title: str) -> MovieMetadata:
        """
        Orchestrate TMDb calls and return a partially-populated
        :class:`MovieMetadata` (missing OMDb fields).
        """
        logger.info("  Fetching TMDb metadata...")
        meta = MovieMetadata(movie=title)

        result = self.search(title)
        if not result:
            logger.warning(f"  TMDb: skipping metadata for '{title}'")
            return meta

        tmdb_id: int = result.get("id", -1)
        meta.tmdb_id = tmdb_id

        # Details (genres, runtime)
        details = self.get_details(tmdb_id)
        genres = [g["name"] for g in details.get("genres", [])]
        meta.genre = ", ".join(genres) if genres else "N/A"
        meta.overview = safe_str(
            details.get("overview") or result.get("overview"), "N/A"
        )
        runtime_min = details.get("runtime")
        if runtime_min:
            meta.runtime = f"{runtime_min} min"

        # Release year
        release_date = result.get("release_date", "")
        meta.year = release_date[:4] if release_date else "N/A"

        # Poster
        poster_path = result.get("poster_path", "")
        if poster_path:
            meta.poster = f"{config.TMDB_IMAGE_BASE_URL}{poster_path}"

        # IMDb ID (stored in details)
        meta.imdb_id = safe_str(details.get("imdb_id"), "N/A")

        # Credits
        credits = self.get_credits(tmdb_id)
        cast = credits.get("cast", [])
        crew = credits.get("crew", [])

        # Top 5 billed actors
        top_actors = [c["name"] for c in cast[:5] if c.get("name")]
        meta.actors = ", ".join(top_actors) if top_actors else "N/A"

        # Director(s)
        directors = [
            c["name"] for c in crew if c.get("job") == "Director" and c.get("name")
        ]
        meta.director = ", ".join(directors) if directors else "N/A"

        return meta


# ─────────────────────────────────────────────────────────────────────────────
# OMDb client
# ─────────────────────────────────────────────────────────────────────────────

class OMDbClient:
    """
    Thin wrapper around the OMDb REST API.

    Parameters
    ----------
    api_key : str
        OMDb API key.
    timeout : int
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str = config.OMDB_API_KEY,
        timeout: int = config.HTTP_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._session = requests.Session()

    def fetch_by_title(self, title: str, year: str | None = None) -> dict[str, Any]:
        """Fetch OMDb data by movie *title* (and optional *year*)."""
        params: dict[str, Any] = {
            "apikey": self._api_key,
            "t": title,
            "type": "movie",
        }
        if year and year != "N/A":
            params["y"] = year
        return self._get(params)

    def fetch_by_imdb_id(self, imdb_id: str) -> dict[str, Any]:
        """Fetch OMDb data by *imdb_id* (e.g. ``tt1375666``)."""
        if not imdb_id or imdb_id == "N/A":
            return {}
        params: dict[str, Any] = {
            "apikey": self._api_key,
            "i": imdb_id,
        }
        return self._get(params)

    def enrich_metadata(
        self, meta: MovieMetadata, *, retry_by_title: bool = True
    ) -> MovieMetadata:
        """
        Supplement *meta* with OMDb data (IMDb rating, runtime fallback).
        Mutates *meta* in-place and returns it.
        """
        logger.info("  Fetching OMDb metadata...")

        # Prefer IMDb-ID lookup; fall back to title
        data = self.fetch_by_imdb_id(meta.imdb_id)
        if not data.get("imdbRating") and retry_by_title:
            data = self.fetch_by_title(meta.movie, meta.year)

        if not data or data.get("Response") == "False":
            logger.warning(f"  OMDb: no data for '{meta.movie}'")
            return meta

        # IMDb rating
        imdb_rating = data.get("imdbRating", "N/A")
        if imdb_rating and imdb_rating != "N/A":
            meta.imdb_rating = imdb_rating

        # Runtime (use OMDb as fallback if TMDb didn't provide it)
        if meta.runtime == "N/A":
            meta.runtime = safe_str(data.get("Runtime"), "N/A")

        # Genre (use OMDb as fallback)
        if meta.genre == "N/A":
            meta.genre = safe_str(data.get("Genre"), "N/A")

        # Director (use OMDb as fallback)
        if meta.director == "N/A":
            meta.director = safe_str(data.get("Director"), "N/A")

        # Actors (use OMDb as fallback)
        if meta.actors == "N/A":
            meta.actors = safe_str(data.get("Actors"), "N/A")

        return meta

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = self._session.get(
                config.OMDB_BASE_URL, params=params, timeout=self._timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.warning(f"  OMDb request failed: {exc}")
            return {}


# ─────────────────────────────────────────────────────────────────────────────
# Unified fetcher
# ─────────────────────────────────────────────────────────────────────────────

class MetadataFetcher:
    """
    Orchestrates TMDb + OMDb calls and returns a fully-merged
    :class:`MovieMetadata` object.

    Parameters
    ----------
    tmdb_client : TMDbClient | None
        Pre-built client (useful for testing / custom keys).
    omdb_client : OMDbClient | None
        Pre-built client (useful for testing / custom keys).
    request_delay : float
        Seconds to sleep between API calls to respect rate limits.
    """

    def __init__(
        self,
        tmdb_client: TMDbClient | None = None,
        omdb_client: OMDbClient | None = None,
        request_delay: float = 0.25,
    ) -> None:
        self._tmdb = tmdb_client or TMDbClient()
        self._omdb = omdb_client or OMDbClient()
        self._delay = request_delay

    def fetch(self, movie_title: str) -> MovieMetadata:
        """
        Fetch and merge metadata for *movie_title*.

        Returns a :class:`MovieMetadata` with all available fields populated.
        Fields that could not be resolved remain as ``"N/A"``.
        """
        # TMDb
        meta = self._tmdb.build_metadata(movie_title)
        time.sleep(self._delay)

        # OMDb
        meta = self._omdb.enrich_metadata(meta)
        time.sleep(self._delay)

        # Log summary
        logger.info(
            f"  Metadata → year={meta.year}, genre={meta.genre}, "
            f"director={meta.director}, imdb={meta.imdb_rating}"
        )
        return meta


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _best_match(
    query: str, results: list[dict[str, Any]], key: str = "title"
) -> dict[str, Any]:
    """
    Return the result whose *key* value best matches *query*.
    Falls back to the first result if no close match is found.
    """
    query_lower = query.lower()
    for item in results:
        if item.get(key, "").lower() == query_lower:
            return item
    # Try partial match
    for item in results:
        if query_lower in item.get(key, "").lower():
            return item
    return results[0]
