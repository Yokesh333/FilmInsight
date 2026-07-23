"""
ingestion_service.py — FilmInsight local ingestion pipeline.

Pipeline flow (no Flowise involved):
    Supabase Storage
        → Download PDF bytes
        → PyMuPDF  (text extraction)
        → RecursiveCharacterTextSplitter  (chunking)
        → Check ChromaDB for duplicate movie embeddings
        → Process in small adaptive batches:
            → HuggingFace Embeddings (via EmbeddingService)
            → Persistent Chroma (local chroma_db/)
        → Return chunk count
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
    # ── Chunking defaults (override via env vars or config) ───────────────────
    CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE",    "800"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "150"))
    BATCH_SIZE    = int(os.environ.get("CHROMA_BATCH_SIZE", "32"))

    # Screenplay-aware separators for RecursiveCharacterTextSplitter
    _SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]

    def __init__(self) -> None:
        from app.core.config import get_settings
        s = self._settings = get_settings()

        self.supabase_url    = (s.SUPABASE_URL or "").rstrip("/")
        self.supabase_key    = s.SUPABASE_SERVICE_ROLE_KEY or ""
        self.supabase_bucket = "movie_scripts"

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
        
        self._splitter = None

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest_from_supabase(
        self,
        supabase_filename: str,
        movie_name: str,
        movie_id: int | None = None,
    ) -> int:
        return self.ingest_movie(
            movie_name=movie_name,
            movie_id=movie_id or -1,
            supabase_filename=supabase_filename
        )

    def ingest_movie(
        self,
        movie_name: str,
        movie_id: int,
        supabase_filename: str | None = None,
        local_pdf_path: str | Path | None = None,
    ) -> int:
        t_start = time.monotonic()
        logger.info(f"[Ingestion] ▶  Starting pipeline for: {movie_name}")

        collection = self._get_chroma_collection()

        # Step 4: Safe Retry - Delete existing vectors for this movie to prevent duplicates
        try:
            existing = collection.get(where={"movie_id": movie_id})
            matched_vectors = len(existing.get("ids", [])) if existing else 0
            logger.info(f"[Ingestion] Deleting vectors: movie_id={movie_id} movie_name={movie_name} matched_vectors={matched_vectors}")
            
            collection.delete(where={"movie_id": movie_id})
            logger.info(f"[Ingestion] Cleared existing Chroma vectors for '{movie_name}' (id={movie_id}) to ensure clean slate.")
        except Exception as exc:
            logger.warning(f"[Ingestion] Failed to clear existing Chroma vectors for '{movie_name}': {exc}")

        # Resolve PDF source
        pdf_bytes = None
        source_name = ""
        
        if supabase_filename:
            # Download from Supabase
            pdf_bytes = self._download_pdf(supabase_filename)
            source_name = f"Supabase/{supabase_filename}"
        elif local_pdf_path:
            local_path = Path(local_pdf_path)
            if local_path.exists():
                pdf_bytes = local_path.read_bytes()
                source_name = f"Local/{local_path.name}"
            else:
                raise IngestionError(f"Local PDF file not found: {local_pdf_path}")
        else:
            raise IngestionError("No PDF source provided (neither Supabase filename nor local path)")

        logger.info(f"[Ingestion] Loaded PDF from {source_name} ({len(pdf_bytes)/1024:.1f} KB)")

        # PyMuPDF text extraction
        pages = self._extract_text(pdf_bytes, movie_name)
        if not pages:
            raise IngestionError("PyMuPDF found no extractable text in the PDF. The PDF may be scanned/image-only.")
        logger.info(f"[Ingestion] Extracted {len(pages)} pages.")

        # Split into chunks
        chunks = self._split_pages(pages)
        if not chunks:
            raise IngestionError("Text splitter produced 0 chunks.")
        logger.info(f"[Ingestion] Split into {len(chunks)} chunks.")

        # Get Rich Metadata (TMDb / OMDb)
        from app.db.database import SessionLocal
        from app.models.movie_script import MovieScript
        
        year = "N/A"
        genres = "N/A"
        director = "N/A"
        actors = "N/A"
        runtime = "N/A"
        rating = "N/A"
        poster_url = "N/A"
        overview = "N/A"
        tmdb_id = -1
        
        with SessionLocal() as db:
            script = db.query(MovieScript).filter(MovieScript.id == movie_id).first()
            if script:
                year = script.release_date[:4] if script.release_date else "N/A"
                genres = script.genres or "N/A"
                runtime = str(script.runtime) if script.runtime else "N/A"
                rating = str(script.rating) if script.rating else "N/A"
                poster_url = script.poster_url or "N/A"
                overview = script.overview or "N/A"
                tmdb_id = script.tmdb_id or -1

        # Generates embeddings and stores in Chroma
        uploaded_at = datetime.now(tz=timezone.utc).isoformat()
        stored = self._embed_and_upsert_batches(
            chunks=chunks,
            movie_name=movie_name,
            movie_id=movie_id,
            uploaded_at=uploaded_at,
            storage_path=supabase_filename or str(local_pdf_path),
            collection=collection,
            year=year,
            genre=genres,
            director=director,
            actors=actors,
            runtime=runtime,
            imdb_rating=rating,
            poster=poster_url,
            overview=overview,
        )

        # Verification step before marking ready
        logger.info(f"[Ingestion] Running post-ingestion verification query for '{movie_name}'…")
        verify_res = collection.get(where={"movie_id": movie_id})
        verify_ids = verify_res.get("ids", [])
        if not verify_ids or len(verify_ids) == 0:
            raise IngestionError("Verification failed: zero vectors retrieved from Chroma after ingestion.")
        
        logger.info(f"[Ingestion] Verification successful: movie_id={movie_id} vectors_found={len(verify_ids)}")
        
        # Verify metadata
        verify_metas = verify_res.get("metadatas", [])
        if verify_metas and verify_metas[0]:
            meta = verify_metas[0]
            if meta.get("movie_name") != movie_name:
                raise IngestionError(f"Verification failed: metadata mismatch. Expected movie_name '{movie_name}', got '{meta.get('movie_name')}'")
        
        elapsed = round((time.monotonic() - t_start), 1)
        logger.info(f"[Ingestion] Verification: PASS. {stored} chunks stored in Chroma. ({elapsed}s total)")
        
        # Structured log (Part 11)
        print(f"\n========================================")
        print(f"Movie: {movie_name}")
        print(f"TMDB ID: {tmdb_id}")
        print(f"Chunks: {len(chunks)}")
        print(f"Vectors Inserted: {stored}")
        print(f"Verification: PASS")
        print(f"Status: READY")
        print(f"========================================\n")
        
        return stored

    # ── Step implementations ──────────────────────────────────────────────────

    def _get_chroma_collection(self):
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:
            raise IngestionError(
                "chromadb is required. Add 'chromadb>=0.5.0' to requirements.txt."
            ) from exc

        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        return client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _download_pdf(self, filename: str) -> bytes:
        url = f"{self.supabase_url}/storage/v1/object/{self.supabase_bucket}/{filename}"
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

    def _extract_text(self, pdf_bytes: bytes, filename: str) -> list[dict[str, Any]]:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise IngestionError("PyMuPDF is required.") from exc

        pages: list[dict[str, Any]] = []
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            doc = fitz.open(tmp_path)
            try:
                for idx in range(len(doc)):
                    page     = doc[idx]
                    raw_text = page.get_text("text")  # type: ignore[attr-defined]
                    if not raw_text or len(raw_text.strip()) < 30:
                        continue
                    text = self._clean_text(raw_text)
                    pages.append({"page_number": idx + 1, "text": text})
            finally:
                doc.close()
        except Exception as exc:
            raise IngestionError(f"PyMuPDF failed to parse '{filename}': {exc}") from exc
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return pages

    def _split_pages(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    def _embed_and_upsert_batches(
        self,
        chunks:      list[dict[str, Any]],
        movie_name:  str,
        movie_id:    int | None,
        uploaded_at: str,
        storage_path: str,
        collection:  Any,
        year: str,
        genre: str,
        director: str,
        actors: str,
        runtime: str,
        imdb_rating: str,
        poster: str,
        overview: str,
    ) -> int:
        from app.services.embedding_service import get_embedder
        embedder = get_embedder()
        
        total_upserted = 0
        n_batches = math.ceil(len(chunks) / self.BATCH_SIZE)

        for i in range(n_batches):
            s = i * self.BATCH_SIZE
            e = s + self.BATCH_SIZE
            batch_chunks = chunks[s:e]
            
            # Generate embeddings for the batch
            try:
                texts = [c["text"] for c in batch_chunks]
                batch_embeddings = embedder.embed_documents(texts)
            except Exception as exc:
                raise IngestionError(f"Embedding generation failed on batch {i+1}: {exc}") from exc
                
            ids:   list[str]           = []
            docs:  list[str]           = []
            metas: list[dict[str, Any]] = []

            for chunk in batch_chunks:
                chunk_index = chunk["chunk_index"]
                safe_movie_id = movie_id if movie_id is not None else -1
                chunk_id    = self._make_chunk_id(safe_movie_id, movie_name, chunk_index)

                meta: dict[str, Any] = {
                    "movie_name":    movie_name,
                    "movie_id":      movie_id if movie_id is not None else -1,
                    "chunk_index":   chunk_index,
                    "page_number":   chunk["page_number"],
                    "uploaded_at":   uploaded_at,
                    "storage_path":  storage_path,
                    "source":        "screenplay",
                    "char_count":    len(chunk["text"]),
                    "year":         year,
                    "genre":        genre,
                    "director":     director,
                    "actors":       actors,
                    "runtime":      runtime,
                    "imdb_rating":  imdb_rating,
                    "poster":       poster,
                    "overview":     overview,
                }

                ids.append(chunk_id)
                docs.append(chunk["text"])
                metas.append(meta)

            logger.info(f"[Ingestion] Upserting vectors: movie_id={movie_id} chunks={len(ids)}")
            collection.upsert(
                ids=ids,
                documents=docs,
                metadatas=metas,
                embeddings=batch_embeddings,
            )
            
            total_upserted += len(ids)
            logger.info(f"[Ingestion]    Chroma batch {i+1}/{n_batches} processed ({total_upserted}/{len(chunks)} chunks)")

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

    @staticmethod
    def _clean_text(text: str) -> str:
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
        import re
        stem = Path(filename).stem
        stem = re.sub(r"[\(\[]\s*\d{4}\s*[\)\]]", "", stem)
        stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)
        stem = re.sub(r"[_.\-]+", " ", stem)
        stem = re.sub(r"\s{2,}", " ", stem).strip()
        return stem.title()

    @staticmethod
    def _make_chunk_id(movie_id: int, movie_name: str, chunk_index: int) -> str:
        import re
        slug = re.sub(r"[^\w]", "_", movie_name.lower()).strip("_")
        slug = re.sub(r"_+", "_", slug)
        return f"m{movie_id}_{slug}_c{chunk_index:06d}"

    @staticmethod
    def _resolve_chroma_dir() -> str:
        here = Path(__file__).resolve().parent
        for candidate in [here.parent.parent, here.parent.parent.parent]:
            chroma = candidate / "chroma_db"
            if chroma.exists():
                return str(chroma)
        return str(here.parent.parent / "chroma_db")


def get_ingestion_service() -> IngestionService:
    return IngestionService()
