"""
chroma_manager.py — Chroma vector-store management for FilmInsight.

Provides a high-level :class:`ChromaManager` that wraps
``chromadb.PersistentClient`` and exposes simple methods to:
  • ensure the collection exists
  • upsert chunks + embeddings in configurable batches
  • query for similar chunks
  • delete all chunks belonging to a movie
  • report collection statistics
"""

from __future__ import annotations

import math
from typing import Any

try:
    import chromadb
    from chromadb import Collection
    from chromadb.config import Settings
except ImportError as exc:
    raise ImportError(
        "chromadb is required. Install with: pip install chromadb"
    ) from exc

from ingestion import config
from ingestion.chunker import Chunk
from ingestion.utils import get_logger

logger = get_logger(__name__)


class ChromaManager:
    """
    Manages a single Chroma collection for screenplay chunks.

    Parameters
    ----------
    persist_directory : str | None
        Path to the Chroma persist directory.  Defaults to
        ``config.CHROMA_DB_DIR``.
    collection_name : str
        Name of the Chroma collection.  Defaults to
        ``config.CHROMA_COLLECTION_NAME``.
    batch_size : int
        Number of documents to upsert per Chroma API call.
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = config.CHROMA_COLLECTION_NAME,
        batch_size: int = config.CHROMA_BATCH_SIZE,
    ) -> None:
        self.persist_directory = persist_directory or str(config.CHROMA_DB_DIR)
        self.collection_name = collection_name
        self.batch_size = batch_size
        self._client: chromadb.ClientAPI | None = None
        self._collection: Collection | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Open a connection to the persistent Chroma store."""
        logger.info(
            f"  Connecting to Chroma at: [bold]{self.persist_directory}[/bold]"
        )
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # cosine distance for MiniLM
        )
        logger.info(
            f"  Collection '{self.collection_name}' ready. "
            f"Existing docs: {self._collection.count()}"
        )

    def close(self) -> None:
        """Release resources (no-op for PersistentClient but good practice)."""
        self._client = None
        self._collection = None

    def __enter__(self) -> "ChromaManager":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Write operations ──────────────────────────────────────────────────────

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        movie_metadata: dict[str, Any],
    ) -> int:
        """
        Upsert *chunks* and their pre-computed *embeddings* into Chroma.

        Each document's metadata is the union of chunk-level metadata
        (``chunk_id``, ``page_number``, …) and *movie_metadata* (genre,
        director, …).

        Parameters
        ----------
        chunks :
            Chunk objects produced by :class:`~ingestion.chunker.ScreenplayChunker`.
        embeddings :
            Parallel list of embedding vectors (same order as *chunks*).
        movie_metadata :
            Flat dict of movie-level metadata (from
            ``MovieMetadata.to_chroma_metadata()``).

        Returns
        -------
        int
            Number of documents successfully upserted.
        """
        self._assert_connected()
        if not chunks:
            return 0

        assert len(chunks) == len(embeddings), (
            f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
        )

        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        vecs: list[list[float]] = []

        for chunk, vector in zip(chunks, embeddings):
            chunk_meta = chunk.to_metadata(extra=movie_metadata)
            # Chroma only accepts str / int / float / bool metadata values
            chunk_meta = _sanitise_metadata(chunk_meta)
            ids.append(chunk.chunk_id)
            docs.append(chunk.text)
            metas.append(chunk_meta)
            vecs.append(vector)

        # Upsert in batches
        total_upserted = 0
        n_batches = math.ceil(len(ids) / self.batch_size)

        for i in range(n_batches):
            s = i * self.batch_size
            e = s + self.batch_size
            self._collection.upsert(  # type: ignore[union-attr]
                ids=ids[s:e],
                documents=docs[s:e],
                metadatas=metas[s:e],
                embeddings=vecs[s:e],
            )
            total_upserted += len(ids[s:e])
            logger.info(
                f"  Upserted batch {i + 1}/{n_batches} "
                f"({total_upserted}/{len(ids)} chunks)"
            )

        return total_upserted

    def delete_movie(self, movie_title: str) -> None:
        """Remove all chunks associated with *movie_title* from the collection."""
        self._assert_connected()
        self._collection.delete(  # type: ignore[union-attr]
            where={"movie_name": movie_title}
        )
        logger.info(f"  Deleted all chunks for '{movie_title}' from Chroma.")

    # ── Read operations ───────────────────────────────────────────────────────

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve the top-*n_results* most similar chunks.

        Parameters
        ----------
        query_embedding :
            Dense query vector.
        n_results :
            Number of nearest neighbours to return.
        where :
            Optional Chroma ``where`` filter (metadata filter).

        Returns
        -------
        dict
            Raw Chroma query response.
        """
        self._assert_connected()
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self._collection.query(**kwargs)  # type: ignore[union-attr]

    def count(self) -> int:
        """Return the total number of documents in the collection."""
        self._assert_connected()
        return self._collection.count()  # type: ignore[union-attr]

    def list_movies(self) -> list[str]:
        """Return a sorted list of unique movie titles in the collection."""
        self._assert_connected()
        result = self._collection.get(  # type: ignore[union-attr]
            include=["metadatas"],
            limit=100_000,
        )
        movies: set[str] = set()
        for meta in result.get("metadatas", []):
            if meta and "movie_name" in meta:
                movies.add(meta["movie_name"])
        return sorted(movies)

    def stats(self) -> dict[str, Any]:
        """Return a summary of the collection."""
        self._assert_connected()
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "total_documents": self.count(),
            "movies": self.list_movies(),
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _assert_connected(self) -> None:
        if self._collection is None:
            raise RuntimeError(
                "ChromaManager is not connected. Call .connect() first "
                "or use it as a context manager."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sanitise_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure every metadata value is a type Chroma accepts
    (``str``, ``int``, ``float``, ``bool``).
    ``None`` and other types are coerced to strings.
    """
    clean: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif v is None:
            clean[k] = "N/A"
        else:
            clean[k] = str(v)
    return clean
