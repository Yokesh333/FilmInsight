"""
ingestion_service.py — FilmInsight local ingestion pipeline.

Pipeline flow (no Flowise involved):
    Supabase Storage
        → Download PDF bytes
        → PyMuPDF  (text extraction)
        → RecursiveCharacterTextSplitter  (chunking)
        → HuggingFace sentence-transformers/all-MiniLM-L6-v2  (embeddings)
        → Persistent Chroma (local chroma_db/)
        → Return chunk count

Every chunk stored in Chroma includes the following metadata:
    • movie_name    – human-readable title parsed from the filename
    • movie_id      – PostgreSQL movie_scripts.id (int)
    • chunk_index   – zero-based chunk position within the document
    • page_number   – source PDF page (1-based)
    • uploaded_at   – ISO-8601 timestamp of when the upload was processed
    • storage_path  – filename as stored in the Supabase bucket

This service is called by the upload router as a FastAPI BackgroundTask.
It NEVER calls any Flowise API.
"""

from __future__ import annotations

import logging
import math
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


# ── Configuration helpers ─────────────────────────────────────────────────────

def _get_env(key: str, default: str = "") -> str:
    """Read from environment; falls back to app settings if available."""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        from app.core.config import get_settings
        return getattr(get_settings(), key, default)
    except Exception:
        return default


# ── Exceptions ────────────────────────────────────────────────────────────────

class IngestionError(Exception):
    """Raised when any step of the local ingestion pipeline fails."""


# ── Main service ──────────────────────────────────────────────────────────────

class IngestionService:
    """
    Orchestrates the full local ingestion pipeline for a single screenplay PDF.

    Components used (all local — no Flowise):
        • requests        – download PDF from Supabase Storage
        • PyMuPDF (fitz)  – extract text page-by-page
        • langchain-text-splitters – RecursiveCharacterTextSplitter
        • sentence-transformers   – HuggingFace all-MiniLM-L6-v2 embeddings
        • chromadb                – PersistentClient vector store
    """

    # ── Chunking defaults (override via env vars or config) ───────────────────
    CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE",    "800"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "150"))
    BATCH_SIZE    = int(os.environ.get("CHROMA_BATCH_SIZE", "100"))

    # Screenplay-aware separators for RecursiveCharacterTextSplitter
    _SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]

    def __init__(self) -> None:
        from app.core.config import get_settings
        s = self._settings = get_settings()

        self.supabase_url    = (s.SUPABASE_URL or "").rstrip("/")
        self.supabase_key    = s.SUPABASE_SERVICE_ROLE_KEY or ""
        self.supabase_bucket = "movie_scripts"

        # Chroma paths — honour Docker env-var overrides
        self.chroma_dir = Path(
            os.environ.get("CHROMA_DB_DIR", "")
            or s.CHROMA_DB_DIR
            or self._resolve_chroma_dir()
        )
        self.collection_name = (
            os.environ.get("CHROMA_COLLECTION_NAME", "")
            or s.CHROMA_COLLECTION_NAME
            or "filminsight_scripts"
        )

        self.embedding_model  = getattr(s, "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_device = getattr(s, "EMBEDDING_DEVICE", "cpu")

        # Lazily loaded — heavy models only initialised on first use
        self._embedder   = None
        self._splitter   = None

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest_from_supabase(
        self,
        supabase_filename: str,
        movie_id: int | None = None,
    ) -> int:
        """
        Download *supabase_filename* from Supabase Storage and run the full
        local ingestion pipeline.

        Parameters
        ----------
        supabase_filename:
            Filename as stored in the Supabase bucket (e.g. ``"Inception.pdf"``).
        movie_id:
            The PostgreSQL ``movie_scripts.id`` — stored as metadata on every chunk.

        Returns
        -------
        int
            Number of chunks stored in Chroma.

        Raises
        ------
        IngestionError
            On download, text-extraction, or Chroma write failures.
        """
        t_start = time.monotonic()
        logger.info(f"[Ingestion] ▶  Starting local pipeline for: {supabase_filename}")

        # Step 1 — Download PDF from Supabase
        pdf_bytes = self._download_pdf(supabase_filename)
        logger.info(
            f"[Ingestion]    Downloaded {len(pdf_bytes) / 1024:.1f} KB "
            f"from Supabase/{self.supabase_bucket}/{supabase_filename}"
        )

        # Step 2 — Extract text using PyMuPDF
        pages = self._extract_text(pdf_bytes, supabase_filename)
        if not pages:
            raise IngestionError(
                f"PyMuPDF found no extractable text in '{supabase_filename}'. "
                "The PDF may be scanned/image-only."
            )
        logger.info(f"[Ingestion]    PyMuPDF extracted {len(pages)} pages.")

        # Step 3 — Split into chunks
        chunks = self._split_pages(pages)
        if not chunks:
            raise IngestionError(
                f"RecursiveCharacterTextSplitter produced 0 chunks for '{supabase_filename}'."
            )
        logger.info(f"[Ingestion]    Split into {len(chunks)} chunks.")

        # Step 4 — Build movie title from filename
        movie_name  = self._filename_to_title(supabase_filename)
        uploaded_at = datetime.now(tz=timezone.utc).isoformat()

        # Step 5 — Generate embeddings
        logger.info(f"[Ingestion]    Generating embeddings for {len(chunks)} chunks…")
        embeddings = self._embed(chunks)
        logger.info(f"[Ingestion]    Embeddings ready ({len(embeddings)} vectors).")

        # Step 6 — Store in Chroma with full metadata
        stored = self._upsert_chroma(
            chunks=chunks,
            embeddings=embeddings,
            movie_name=movie_name,
            movie_id=movie_id,
            uploaded_at=uploaded_at,
            storage_path=supabase_filename,
        )

        elapsed = round((time.monotonic() - t_start), 1)
        logger.info(
            f"[Ingestion] ✔  '{movie_name}' — {stored} chunks stored in Chroma. "
            f"({elapsed}s total)"
        )
        return stored

    # ── Step implementations ──────────────────────────────────────────────────

    def _download_pdf(self, filename: str) -> bytes:
        """Download a PDF from Supabase Storage and return its raw bytes."""
        url = (
            f"{self.supabase_url}/storage/v1/object"
            f"/{self.supabase_bucket}/{filename}"
        )
        headers = {
            "apikey":        self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=120)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            raise IngestionError(
                f"Failed to download '{filename}' from Supabase: {exc}"
            ) from exc

    def _extract_text(
        self, pdf_bytes: bytes, filename: str
    ) -> list[dict[str, Any]]:
        """
        Use PyMuPDF to extract text page-by-page.

        Returns a list of dicts: ``{"page_number": int, "text": str}``.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise IngestionError(
                "PyMuPDF is required. Add 'PyMuPDF>=1.23.0' to requirements.txt."
            ) from exc

        pages: list[dict[str, Any]] = []
        try:
            # Write bytes to a temp file so fitz.open() works cross-platform
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            doc = fitz.open(tmp_path)
            try:
                for idx in range(len(doc)):
                    page     = doc[idx]
                    raw_text = page.get_text("text")  # type: ignore[attr-defined]
                    if not raw_text or len(raw_text.strip()) < 30:
                        continue  # skip blank / image-only pages
                    text = self._clean_text(raw_text)
                    pages.append({"page_number": idx + 1, "text": text})
            finally:
                doc.close()
        except Exception as exc:
            raise IngestionError(
                f"PyMuPDF failed to parse '{filename}': {exc}"
            ) from exc
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return pages

    def _split_pages(
        self, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Apply RecursiveCharacterTextSplitter to each page.

        Returns a flat list of chunk dicts:
            ``{"text": str, "page_number": int, "chunk_index": int}``
        """
        splitter = self._get_splitter()
        result: list[dict[str, Any]] = []
        global_idx = 0

        for page in pages:
            splits = splitter.split_text(page["text"])
            for fragment in splits:
                fragment = fragment.strip()
                if not fragment:
                    continue
                result.append({
                    "text":        fragment,
                    "page_number": page["page_number"],
                    "chunk_index": global_idx,
                })
                global_idx += 1

        return result

    def _embed(self, chunks: list[dict[str, Any]]) -> list[list[float]]:
        """Generate embeddings for all chunks using HuggingFace sentence-transformers."""
        embedder = self._get_embedder()
        texts    = [c["text"] for c in chunks]
        try:
            return embedder.embed_documents(texts)
        except Exception as exc:
            raise IngestionError(f"Embedding generation failed: {exc}") from exc

    def _upsert_chroma(
        self,
        chunks:      list[dict[str, Any]],
        embeddings:  list[list[float]],
        movie_name:  str,
        movie_id:    int | None,
        uploaded_at: str,
        storage_path: str,
    ) -> int:
        """
        Upsert chunks + embeddings into the persistent Chroma collection.

        Each document's metadata includes:
            movie_name, movie_id, chunk_index, page_number,
            uploaded_at, storage_path
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:
            raise IngestionError(
                "chromadb is required. Add 'chromadb>=0.5.0' to requirements.txt."
            ) from exc

        self.chroma_dir.mkdir(parents=True, exist_ok=True)

        client     = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids:   list[str]           = []
        docs:  list[str]           = []
        metas: list[dict[str, Any]] = []
        vecs:  list[list[float]]   = []

        for chunk, vector in zip(chunks, embeddings):
            chunk_index = chunk["chunk_index"]
            chunk_id    = self._make_chunk_id(movie_name, chunk_index)

            meta: dict[str, Any] = {
                "movie_name":    movie_name,
                "movie_id":      movie_id if movie_id is not None else -1,
                "chunk_index":   chunk_index,
                "page_number":   chunk["page_number"],
                "uploaded_at":   uploaded_at,
                "storage_path":  storage_path,
                "source":        "screenplay",
                "char_count":    len(chunk["text"]),
            }

            ids.append(chunk_id)
            docs.append(chunk["text"])
            metas.append(meta)
            vecs.append(vector)

        # Upsert in batches to avoid memory spikes on large screenplays
        total_upserted = 0
        n_batches      = math.ceil(len(ids) / self.BATCH_SIZE)

        for i in range(n_batches):
            s = i * self.BATCH_SIZE
            e = s + self.BATCH_SIZE
            collection.upsert(
                ids=ids[s:e],
                documents=docs[s:e],
                metadatas=metas[s:e],
                embeddings=vecs[s:e],
            )
            total_upserted += len(ids[s:e])
            logger.info(
                f"[Ingestion]    Chroma batch {i+1}/{n_batches} "
                f"({total_upserted}/{len(ids)} chunks)"
            )

        return total_upserted

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_splitter(self):
        if self._splitter is None:
            try:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.CHUNK_SIZE,
                chunk_overlap=self.CHUNK_OVERLAP,
                separators=self._SEPARATORS,
                length_function=len,
                is_separator_regex=False,
            )
        return self._splitter

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore
            logger.info(
                f"[Ingestion]    Loading embedding model: "
                f"{self.embedding_model} (device={self.embedding_device})"
            )
            self._embedder = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={"device": self.embedding_device},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embedder

    @staticmethod
    def _clean_text(text: str) -> str:
        """Light-touch cleaning: normalize line endings and collapse excess blank lines."""
        import re
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[^\x09\x0A\x20-\x7E\x80-\xFF]", "", text)
        lines = [line.rstrip() for line in text.splitlines()]
        cleaned: list[str] = []
        blank_run = 0
        for line in lines:
            if line == "":
                blank_run += 1
                if blank_run <= 2:
                    cleaned.append(line)
            else:
                blank_run = 0
                cleaned.append(line)
        return "\n".join(cleaned).strip()

    @staticmethod
    def _filename_to_title(filename: str) -> str:
        """Convert a bucket filename into a human-readable title."""
        import re
        stem = Path(filename).stem
        stem = re.sub(r"[\(\[]\s*\d{4}\s*[\)\]]", "", stem)
        stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)
        stem = re.sub(r"[_.\-]+", " ", stem)
        stem = re.sub(r"\s{2,}", " ", stem).strip()
        return stem.title()

    @staticmethod
    def _make_chunk_id(movie_name: str, chunk_index: int) -> str:
        """Generate a deterministic, filesystem-safe chunk ID."""
        import re
        slug = re.sub(r"[^\w]", "_", movie_name.lower()).strip("_")
        slug = re.sub(r"_+", "_", slug)
        return f"{slug}_c{chunk_index:06d}"

    @staticmethod
    def _resolve_chroma_dir() -> str:
        """Walk up from this file to find the project-root chroma_db/."""
        here = Path(__file__).resolve().parent
        for candidate in [here.parent.parent, here.parent.parent.parent]:
            chroma = candidate / "chroma_db"
            if chroma.exists():
                return str(chroma)
        # Default: project root sibling of backend/
        return str(here.parent.parent / "chroma_db")


def get_ingestion_service() -> IngestionService:
    """FastAPI dependency factory."""
    return IngestionService()
