"""
pdf_loader.py — PDF text extraction for the FilmInsight ingestion pipeline.

Uses PyMuPDF (fitz) to extract text from screenplay PDFs page by page,
preserving page-number metadata for downstream chunk attribution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

try:
    import fitz  # PyMuPDF
except ImportError as exc:
    raise ImportError(
        "PyMuPDF is required. Install it with: pip install pymupdf"
    ) from exc

from ingestion.utils import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PageContent:
    """Represents the extracted text of a single PDF page."""
    page_number: int        # 1-based
    text: str               # raw extracted text


@dataclass
class LoadedDocument:
    """Result of loading a complete PDF screenplay."""
    title: str
    pdf_path: Path
    pages: list[PageContent] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenation of all page texts."""
        return "\n".join(p.text for p in self.pages)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_characters(self) -> int:
        return sum(len(p.text) for p in self.pages)


# ─────────────────────────────────────────────────────────────────────────────
# PDF Loader class
# ─────────────────────────────────────────────────────────────────────────────

class PDFLoader:
    """
    Loads and extracts text from a screenplay PDF using PyMuPDF.

    Parameters
    ----------
    max_pages : int | None
        Maximum number of pages to read. ``None`` reads all pages.
    min_chars_per_page : int
        Pages with fewer characters than this threshold are skipped
        (e.g., blank pages or pure image pages).
    clean_text : bool
        If ``True``, apply light text-cleaning heuristics after extraction.
    """

    def __init__(
        self,
        max_pages: int | None = None,
        min_chars_per_page: int = 30,
        clean_text: bool = True,
    ) -> None:
        self.max_pages = max_pages
        self.min_chars_per_page = min_chars_per_page
        self.clean_text = clean_text

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, pdf_path: Path, title: str) -> LoadedDocument:
        """
        Extract text from *pdf_path* and return a :class:`LoadedDocument`.

        Raises
        ------
        FileNotFoundError
            If *pdf_path* does not exist.
        RuntimeError
            If PyMuPDF cannot open the file.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"  Opening PDF: [bold]{pdf_path.name}[/bold]")

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as exc:
            raise RuntimeError(f"Cannot open {pdf_path}: {exc}") from exc

        pages: list[PageContent] = []

        try:
            total = min(len(doc), self.max_pages) if self.max_pages else len(doc)
            logger.info(f"  Pages to read: {total}")

            for page_idx in range(total):
                page = doc[page_idx]
                raw_text = page.get_text("text")  # type: ignore[attr-defined]

                if not raw_text or len(raw_text.strip()) < self.min_chars_per_page:
                    continue  # skip blank / image-only pages

                text = self._clean(raw_text) if self.clean_text else raw_text
                pages.append(PageContent(page_number=page_idx + 1, text=text))
        finally:
            doc.close()

        loaded = LoadedDocument(title=title, pdf_path=pdf_path, pages=pages)
        logger.info(
            f"  Extracted {loaded.page_count} pages "
            f"({loaded.total_characters:,} chars) from '{title}'"
        )
        return loaded

    # ── Page iteration ────────────────────────────────────────────────────────

    def iter_pages(self, pdf_path: Path) -> Iterator[PageContent]:
        """Yield :class:`PageContent` objects one page at a time."""
        doc = fitz.open(str(pdf_path))
        try:
            total = (
                min(len(doc), self.max_pages) if self.max_pages else len(doc)
            )
            for page_idx in range(total):
                raw_text = doc[page_idx].get_text("text")  # type: ignore[attr-defined]
                if raw_text and len(raw_text.strip()) >= self.min_chars_per_page:
                    text = self._clean(raw_text) if self.clean_text else raw_text
                    yield PageContent(page_number=page_idx + 1, text=text)
        finally:
            doc.close()

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """
        Light-touch cleaning:
        • Collapse runs of blank lines (≥3) to two newlines.
        • Strip trailing whitespace from each line.
        • Remove non-printable control characters (except newline / tab).
        """
        # Remove carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip control chars (keep \n and \t)
        text = re.sub(r"[^\x09\x0A\x20-\x7E\x80-\xFF]", "", text)

        # Strip trailing spaces on each line
        lines = [line.rstrip() for line in text.splitlines()]

        # Collapse ≥3 consecutive blank lines → 2 blank lines
        cleaned_lines: list[str] = []
        blank_run = 0
        for line in lines:
            if line == "":
                blank_run += 1
                if blank_run <= 2:
                    cleaned_lines.append(line)
            else:
                blank_run = 0
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function
# ─────────────────────────────────────────────────────────────────────────────

def load_screenplay(
    pdf_path: Path,
    title: str,
    max_pages: int | None = None,
) -> LoadedDocument:
    """One-shot helper: load a single PDF and return a :class:`LoadedDocument`."""
    loader = PDFLoader(max_pages=max_pages)
    return loader.load(pdf_path, title)
