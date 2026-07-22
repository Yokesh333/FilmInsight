"""
rag_service.py — Local RAG service for FilmInsight.

Architecture:
    User Question
        → Embed query (HuggingFace all-MiniLM-L6-v2)
        → Chroma similarity search  (k=5)
        → Deduplicate + rank chunks
        → Build structured RAG prompt
        → Groq LLM  (llama-3.3-70b-versatile)
        → Structured ChatResponse

The Chroma collection is opened once per process via a module-level singleton.
Every query can optionally filter by ``movie_name`` metadata so the retriever
returns only chunks from the specific movie the user is asking about.
"""

from __future__ import annotations

import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Singleton: shared embedder + Chroma client ────────────────────────────────

_embedder   = None
_chroma_col = None   # chromadb.Collection


def _get_embedder():
    """Load the HuggingFace embedding model once per process."""
    global _embedder
    if _embedder is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore

        from app.core.config import get_settings
        s      = get_settings()
        model  = getattr(s, "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        device = getattr(s, "EMBEDDING_DEVICE", "cpu")

        logger.info(f"[RAG] Loading embedding model: {model} (device={device})")
        _embedder = HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("[RAG] Embedding model ready.")
    return _embedder


def _get_chroma_collection():
    """Open the persistent Chroma collection once per process."""
    global _chroma_col
    if _chroma_col is None:
        import chromadb
        from chromadb.config import Settings
        from app.core.config import get_settings

        s       = get_settings()
        chroma_dir = Path(
            os.environ.get("CHROMA_DB_DIR", "")
            or getattr(s, "CHROMA_DB_DIR", "")
            or _resolve_chroma_dir()
        )
        col_name = (
            os.environ.get("CHROMA_COLLECTION_NAME", "")
            or getattr(s, "CHROMA_COLLECTION_NAME", "filminsight_scripts")
        )

        logger.info(f"[RAG] Opening Chroma at: {chroma_dir}  collection='{col_name}'")
        client      = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        _chroma_col = client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"[RAG] Chroma ready — {_chroma_col.count()} documents.")
    return _chroma_col


def _resolve_chroma_dir() -> str:
    here = Path(__file__).resolve().parent
    for candidate in [here.parent.parent, here.parent.parent.parent]:
        chroma = candidate / "chroma_db"
        if chroma.exists():
            return str(chroma)
    return str(here.parent.parent / "chroma_db")


# ── RAG Service ───────────────────────────────────────────────────────────────

class RAGService:
    """
    Local Retrieval-Augmented Generation service.

    1. Embed the user question with HuggingFace all-MiniLM-L6-v2
    2. Similarity search Chroma with k=5 (optionally filtered by movie_name)
    3. Deduplicate returned chunks (exact-text comparison)
    4. Assemble a clean, structured RAG prompt
    5. Call Groq Chat Completion API
    6. Return answer text + source documents
    """

    # Number of nearest-neighbour chunks to retrieve
    TOP_K: int = 5

    def __init__(self) -> None:
        from app.core.config import get_settings
        s = get_settings()
        self.groq_api_key = getattr(s, "GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
        self.groq_model   = getattr(s, "GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── Public API ────────────────────────────────────────────────────────────

    async def query(
        self,
        question:   str,
        session_id: str,
        movie_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the full RAG pipeline for a single user question.

        Parameters
        ----------
        question:
            The user's natural-language question.
        session_id:
            Frontend session UUID (passed through to the response).
        movie_name:
            If provided, Chroma search is filtered to chunks from this movie.

        Returns
        -------
        dict with keys: ``answer``, ``sources``, ``session_id``, ``movie_title``
        """
        t0 = time.monotonic()

        # Step 1 — Embed the query
        query_vector = self._embed_query(question)

        # Step 2 — Retrieve top-K chunks from Chroma
        raw_results = self._retrieve(query_vector, movie_name=movie_name)

        # Step 3 — Deduplicate & format context
        chunks = self._deduplicate(raw_results)

        # Step 4 — Build RAG prompt
        prompt = self._build_prompt(question, chunks, movie_name)

        # Step 5 — Call Groq
        answer = await self._call_groq(prompt)

        # Step 6 — Format source documents
        sources = self._format_sources(chunks)

        elapsed_ms = round((time.monotonic() - t0) * 1000)
        logger.info(
            f"[RAG] Query answered in {elapsed_ms}ms  "
            f"(chunks={len(chunks)}, movie={movie_name or 'any'})"
        )

        return {
            "answer":      answer,
            "sources":     sources,
            "session_id":  session_id,
            "movie_title": movie_name,
        }

    def chroma_doc_count(self) -> int:
        """Return the total number of documents in Chroma (for health checks)."""
        try:
            return _get_chroma_collection().count()
        except Exception:
            return 0

    # ── Internal steps ────────────────────────────────────────────────────────

    def _embed_query(self, question: str) -> list[float]:
        """Embed the question string using the shared HuggingFace model."""
        try:
            return _get_embedder().embed_query(question)
        except Exception as exc:
            logger.error(f"[RAG] Embedding failed: {exc}")
            raise

    def _retrieve(
        self,
        query_vector: list[float],
        movie_name:   str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform cosine similarity search in Chroma.

        If *movie_name* is supplied the search is scoped to that movie's chunks
        via a Chroma ``where`` metadata filter.

        Returns a list of result dicts with ``text``, ``metadata``, ``distance``.
        """
        col    = _get_chroma_collection()
        total  = col.count()

        if total == 0:
            logger.warning("[RAG] Chroma collection is empty — no context available.")
            return []

        # Use a slightly larger k so deduplication doesn't shrink us below 5
        fetch_k = min(max(self.TOP_K + 3, 8), total)

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results":        fetch_k,
            "include":          ["documents", "metadatas", "distances"],
        }

        # Metadata filter: restrict to a specific movie when requested
        if movie_name:
            kwargs["where"] = {"movie_name": {"$eq": movie_name}}

        try:
            raw = col.query(**kwargs)
        except Exception as exc:
            logger.warning(
                f"[RAG] Filtered query failed ({exc}), falling back to unfiltered search."
            )
            kwargs.pop("where", None)
            raw = col.query(**kwargs)

        results: list[dict[str, Any]] = []
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances",  [[]])[0]

        for text, meta, dist in zip(documents, metadatas, distances):
            if text:
                results.append({
                    "text":     text,
                    "metadata": meta or {},
                    "score":    round(1.0 - dist, 4),  # convert distance → similarity
                })

        return results

    @staticmethod
    def _deduplicate(
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Remove exact-duplicate chunks (same text) and return at most TOP_K items,
        sorted by descending similarity score.
        """
        seen:   set[str]           = set()
        unique: list[dict[str, Any]] = []

        for item in sorted(results, key=lambda x: x["score"], reverse=True):
            text_key = item["text"].strip()
            if text_key not in seen:
                seen.add(text_key)
                unique.append(item)

        return unique[:RAGService.TOP_K]

    @staticmethod
    def _build_prompt(
        question:   str,
        chunks:     list[dict[str, Any]],
        movie_name: str | None,
    ) -> str:
        """
        Assemble a structured RAG prompt that:
        • Explains the assistant's role
        • Embeds retrieved screenplay context with source attribution
        • States the user's question clearly
        • Provides output instructions
        """
        movie_context_line = (
            f"The user is asking about the movie: **{movie_name}**.\n"
            if movie_name else ""
        )

        if chunks:
            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                meta        = chunk.get("metadata", {})
                page_num    = meta.get("page_number", "?")
                chunk_movie = meta.get("movie_name", movie_name or "Unknown")
                score       = chunk.get("score", 0)
                context_parts.append(
                    f"[Chunk {i} | Movie: {chunk_movie} | Page: {page_num} | Relevance: {score:.2f}]\n"
                    f"{chunk['text']}"
                )
            context_block = "\n\n---\n\n".join(context_parts)
        else:
            context_block = "(No screenplay context was found for this query.)"

        prompt = f"""You are FilmInsight, an expert AI movie assistant with deep knowledge of screenplays and cinema.

{movie_context_line}
## Retrieved Screenplay Context

{context_block}

---

## User Question

{question}

---

## Instructions

- Answer the question using the screenplay context above as your primary source.
- If the context contains relevant information, cite it naturally in your answer (e.g. "In the screenplay…", "According to the script…").
- If additional information such as cast, release year, IMDb rating, box office, or trivia is relevant, include it under a separate "Additional Info" heading.
- Do NOT copy screenplay text verbatim in large blocks — synthesize and explain.
- If the screenplay context is insufficient, clearly acknowledge that and provide what general knowledge you have.
- Never fabricate screenplay events or character actions that are not in the context.
- Keep your answer clear, engaging, and appropriately concise.
"""
        return prompt.strip()

    async def _call_groq(self, prompt: str) -> str:
        """
        Send the RAG prompt to the Groq Chat Completion API.

        Falls back to a context-only summary if no API key is configured.
        """
        if not self.groq_api_key:
            logger.warning(
                "[RAG] GROQ_API_KEY is not set. "
                "Returning context-only response (no LLM generation)."
            )
            return (
                "⚠️ Groq API key is not configured. "
                "Please set GROQ_API_KEY in backend/.env to enable AI-generated answers. "
                "Screenplay context was retrieved successfully from the local Chroma database."
            )

        import httpx

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":    self.groq_model,
            "messages": [
                {
                    "role":    "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.4,
            "max_tokens":  1024,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0)
            ) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

            if resp.status_code != 200:
                logger.error(
                    f"[RAG] Groq error {resp.status_code}: {resp.text[:400]}"
                )
                raise RuntimeError(
                    f"Groq API error {resp.status_code}: {resp.text[:200]}"
                )

            data   = resp.json()
            answer = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )
            return answer or "I could not generate a response. Please try again."

        except httpx.TimeoutException:
            raise RuntimeError(
                "Groq request timed out after 90 seconds. Please try again."
            )
        except httpx.ConnectError:
            raise RuntimeError(
                "Cannot connect to Groq API. Check your internet connection."
            )

    @staticmethod
    def _format_sources(
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Convert deduplicated chunks into SourceDocument-compatible dicts.

        Preserves all Chroma metadata fields for the frontend.
        """
        sources = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            sources.append({
                "pageLabel":   (
                    meta.get("movie_name")
                    or f"Page {meta.get('page_number', '?')}"
                ),
                "content":     chunk["text"][:600],
                "page":        meta.get("page_number"),
                "score":       chunk.get("score"),
                # Extra metadata preserved for the frontend
                "movie_name":   meta.get("movie_name"),
                "movie_id":     meta.get("movie_id"),
                "chunk_index":  meta.get("chunk_index"),
                "uploaded_at":  meta.get("uploaded_at"),
                "storage_path": meta.get("storage_path"),
            })
        return sources


# ── Singleton accessor ────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """FastAPI dependency — returns the singleton RAGService."""
    return RAGService()
