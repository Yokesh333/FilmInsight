"""
chunker.py — Semantic text chunking for the FilmInsight ingestion pipeline.

Splits screenplay pages into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, preserving page-number attribution
so each chunk can be traced back to its source page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        # Older LangChain (< 0.2) bundled splitters in langchain.text_splitter
        from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]
    except ImportError as exc:
        raise ImportError(
            "LangChain text splitters are required. "
            "Install with: pip install langchain-text-splitters"
        ) from exc

from ingestion.pdf_loader import LoadedDocument, PageContent
from ingestion.utils import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    """A single text chunk ready for embedding and storage."""
    chunk_id: str           # globally unique identifier
    movie_title: str
    page_number: int        # source page (1-based)
    text: str
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)

    def to_metadata(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Return a flat metadata dict suitable for Chroma.
        *extra* is merged in (movie-level metadata goes here).
        """
        meta: dict[str, Any] = {
            "chunk_id": self.chunk_id,
            "movie_name": self.movie_title,
            "page_number": self.page_number,
            "source": "screenplay",
            "char_count": self.char_count,
        }
        if extra:
            meta.update(extra)
        return meta


# ─────────────────────────────────────────────────────────────────────────────
# Chunker class
# ─────────────────────────────────────────────────────────────────────────────

class ScreenplayChunker:
    """
    Splits a :class:`~ingestion.pdf_loader.LoadedDocument` into
    :class:`Chunk` objects using :class:`RecursiveCharacterTextSplitter`.

    The splitter uses screenplay-aware separators so it tries to break on
    scene boundaries (``\n\n\n``, ``\n\n``) before resorting to sentence-
    level breaks.

    Parameters
    ----------
    chunk_size : int
        Target character count per chunk.
    chunk_overlap : int
        Number of overlapping characters between adjacent chunks.
    """

    # Separators ordered from coarsest to finest granularity
    _SEPARATORS: list[str] = [
        "\n\n\n",   # scene breaks (triple blank line in screenplays)
        "\n\n",     # paragraph / slug-line breaks
        "\n",       # single newline
        ". ",       # sentence boundary
        "! ",
        "? ",
        ", ",
        " ",        # word boundary (last resort)
        "",         # character boundary (absolute last resort)
    ]

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self._SEPARATORS,
            length_function=len,
            is_separator_regex=False,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def chunk_document(self, document: LoadedDocument) -> list[Chunk]:
        """
        Chunk every page of *document* and return a flat list of
        :class:`Chunk` objects ordered by page number.
        """
        all_chunks: list[Chunk] = []

        for page in document.pages:
            page_chunks = self._chunk_page(page, document.title)
            all_chunks.extend(page_chunks)

        logger.info(
            f"  Chunked '{document.title}' → "
            f"{len(all_chunks)} chunks across {document.page_count} pages"
        )
        return all_chunks

    def chunk_pages(
        self, pages: list[PageContent], movie_title: str
    ) -> list[Chunk]:
        """Chunk a list of :class:`PageContent` objects directly."""
        all_chunks: list[Chunk] = []
        for page in pages:
            all_chunks.extend(self._chunk_page(page, movie_title))
        return all_chunks

    # ── Private helpers ───────────────────────────────────────────────────────

    def _chunk_page(self, page: PageContent, movie_title: str) -> list[Chunk]:
        """Split a single page into chunks and assign unique IDs."""
        if not page.text.strip():
            return []

        raw_splits: list[str] = self._splitter.split_text(page.text)

        chunks: list[Chunk] = []
        for idx, text in enumerate(raw_splits):
            text = text.strip()
            if not text:
                continue
            chunk_id = _make_chunk_id(movie_title, page.page_number, idx)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    movie_title=movie_title,
                    page_number=page.page_number,
                    text=text,
                )
            )
        return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_chunk_id(movie_title: str, page_number: int, chunk_index: int) -> str:
    """
    Build a deterministic, filesystem-safe chunk ID.

    Format: ``<slug>_p<page>_c<index>``
    """
    import re
    slug = re.sub(r"[^\w]", "_", movie_title.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return f"{slug}_p{page_number:04d}_c{chunk_index:04d}"


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function
# ─────────────────────────────────────────────────────────────────────────────

def chunk_screenplay(
    document: LoadedDocument,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    """One-shot helper: chunk a loaded screenplay document."""
    chunker = ScreenplayChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_document(document)
