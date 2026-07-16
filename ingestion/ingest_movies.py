"""
ingest_movies.py — Entry-point for the FilmInsight ingestion pipeline.

Usage
-----
    python -m ingestion.ingest_movies
    # or
    python ingestion/ingest_movies.py

The script orchestrates the full pipeline for each unprocessed movie:

    1.  Scan  movie_scripts/ for PDF files
    2.  Skip  PDFs already listed in processed_movies.json
    3.  Load  text from PDF using PyMuPDF  (pdf_loader)
    4.  Chunk text into overlapping segments (chunker)
    5.  Fetch metadata from TMDb + OMDb     (metadata_fetcher)
    6.  Embed chunks via HuggingFace        (embedding_generator)
    7.  Store chunks + embeddings in Chroma (chroma_manager)
    8.  Mark  movie as processed            (utils)

The pipeline is fully resumable: if it is interrupted at any point,
re-running will pick up only from the first un-processed movie.
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path
from typing import Any

# ── Local imports ─────────────────────────────────────────────────────────────
from ingestion import config
from ingestion.chunker import ScreenplayChunker
from ingestion.chroma_manager import ChromaManager
from ingestion.embedding_generator import EmbeddingGenerator
from ingestion.metadata_fetcher import MetadataFetcher
from ingestion.pdf_loader import PDFLoader
from ingestion.utils import (
    discover_new_pdfs,
    get_logger,
    load_processed_movies,
    mark_movie_processed,
    scan_pdf_files,
)

logger = get_logger("filminsight.ingest")


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline class
# ─────────────────────────────────────────────────────────────────────────────

class IngestionPipeline:
    """
    Orchestrates the full ingestion workflow.

    Parameters
    ----------
    scripts_dir : Path
        Directory containing screenplay PDFs.
    chroma_dir : Path
        Chroma persistence directory.
    processed_file : Path
        JSON file tracking already-ingested movies.
    chunk_size : int
        Target characters per text chunk.
    chunk_overlap : int
        Character overlap between consecutive chunks.
    embedding_model : str
        HuggingFace sentence-transformer model name.
    embedding_device : str
        Device for embedding inference (``"cpu"`` / ``"cuda"`` / ``"mps"``).
    """

    def __init__(
        self,
        scripts_dir: Path = config.MOVIE_SCRIPTS_DIR,
        chroma_dir: Path = config.CHROMA_DB_DIR,
        processed_file: Path = config.PROCESSED_MOVIES_FILE,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
        embedding_model: str = config.EMBEDDING_MODEL_NAME,
        embedding_device: str = config.EMBEDDING_DEVICE,
    ) -> None:
        self.scripts_dir = scripts_dir
        self.processed_file = processed_file

        # Lazily-initialised components
        self._pdf_loader = PDFLoader(max_pages=config.MAX_PAGES)
        self._chunker = ScreenplayChunker(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self._metadata_fetcher = MetadataFetcher()
        self._embedder = EmbeddingGenerator(
            model_name=embedding_model, device=embedding_device
        )
        self._chroma = ChromaManager(persist_directory=str(chroma_dir))

    # ── Main entry-point ──────────────────────────────────────────────────────

    def run(self) -> None:
        """Execute the full ingestion pipeline."""
        start_time = time.time()

        # ── 1. Scan for PDFs ──────────────────────────────────────────────────
        logger.info("")
        logger.info("=" * 60)
        logger.info("  FilmInsight — Ingestion Pipeline")
        logger.info("=" * 60)
        logger.info(f"\nScanning {self.scripts_dir}...")

        all_pdfs = scan_pdf_files(self.scripts_dir)
        logger.info(f"Found {len(all_pdfs)} PDF(s) in total.")

        # ── 2. Load registry & discover new movies ────────────────────────────
        registry = load_processed_movies(self.processed_file)
        new_movies = discover_new_pdfs(self.scripts_dir, registry)

        if not new_movies:
            logger.info(
                "[success]All movies already ingested. Nothing to do.[/success]"
            )
            return

        logger.info(
            f"[info]{len(new_movies)} new movie(s) to process.[/info]"
        )

        # ── 3. Open Chroma connection (shared for all movies) ─────────────────
        self._chroma.connect()

        # ── 4. Process each new movie ─────────────────────────────────────────
        success_count = 0
        failure_count = 0

        for movie_idx, (pdf_path, title, record_id) in enumerate(new_movies, start=1):
            logger.info("")
            logger.info(
                f"[{'─' * 58}]"
            )
            logger.info(
                f"  [{movie_idx}/{len(new_movies)}] Processing [bold]{title}[/bold]..."
            )

            try:
                chunks_stored = self._process_one_movie(pdf_path, title)
                mark_movie_processed(
                    registry,
                    title,
                    self.processed_file,
                    chunks_stored,
                    str(pdf_path),
                    record_id
                )
                logger.info(
                    f"  [success]✓ '{title}' → {chunks_stored} chunks stored.[/success]"
                )
                success_count += 1

            except KeyboardInterrupt:
                logger.warning("\nInterrupted by user. Progress has been saved.")
                sys.exit(0)

            except Exception as exc:  # noqa: BLE001
                failure_count += 1
                logger.error(
                    f"  [error]✗ Failed to process '{title}': {exc}[/error]"
                )
                if config.STRICT_METADATA:
                    raise
                traceback.print_exc()
                continue
                
            finally:
                try:
                    if pdf_path.exists():
                        pdf_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {pdf_path}: {e}")

        # ── 5. Summary ────────────────────────────────────────────────────────
        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=" * 60)
        logger.info(
            f"  Done. "
            f"{success_count} succeeded, {failure_count} failed. "
            f"Total time: {elapsed:.1f}s"
        )
        stats = self._chroma.stats()
        logger.info(
            f"  Chroma collection '{stats['collection_name']}': "
            f"{stats['total_documents']} total documents."
        )
        logger.info("=" * 60)
        logger.info("")

    # ── Per-movie logic ───────────────────────────────────────────────────────

    def _process_one_movie(self, pdf_path: Path, title: str) -> int:
        """
        Run the full pipeline for a single movie.

        Returns the number of chunks stored in Chroma.
        """
        # Step A: Load PDF
        document = self._pdf_loader.load(pdf_path, title)

        if document.page_count == 0:
            raise ValueError(f"No readable text found in '{pdf_path.name}'")

        # Step B: Chunk text
        chunks = self._chunker.chunk_document(document)
        if not chunks:
            raise ValueError(f"No chunks produced for '{title}'")

        # Step C: Fetch metadata
        movie_meta = self._metadata_fetcher.fetch(title)
        chroma_movie_meta = movie_meta.to_chroma_metadata()

        # Step D: Generate embeddings
        logger.info(f"  Generating embeddings for {len(chunks)} chunks...")
        embeddings = self._embedder.embed_chunks(chunks)

        # Step E: Upsert into Chroma
        chunks_stored = self._chroma.upsert_chunks(
            chunks=chunks,
            embeddings=embeddings,
            movie_metadata=chroma_movie_meta,
        )

        logger.info(f"  Stored {chunks_stored} chunks.")
        return chunks_stored


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Parse optional CLI arguments and run the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ingest_movies",
        description="FilmInsight — Automated screenplay ingestion pipeline",
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=config.MOVIE_SCRIPTS_DIR,
        help="Directory containing screenplay PDFs (default: movie_scripts/)",
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=config.CHROMA_DB_DIR,
        help="Chroma persistence directory (default: chroma_db/)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=config.CHUNK_SIZE,
        help=f"Chunk character size (default: {config.CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=config.CHUNK_OVERLAP,
        help=f"Chunk overlap characters (default: {config.CHUNK_OVERLAP})",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=config.EMBEDDING_DEVICE,
        choices=["cpu", "cuda", "mps"],
        help="Embedding device (default: cpu)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Abort on first metadata fetch failure",
    )

    args = parser.parse_args()

    # Override config at runtime if strict flag is set
    if args.strict:
        config.STRICT_METADATA = True

    pipeline = IngestionPipeline(
        scripts_dir=args.scripts_dir,
        chroma_dir=args.chroma_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedding_device=args.device,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
