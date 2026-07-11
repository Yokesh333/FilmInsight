"""
embedding_generator.py — HuggingFace embedding generation for FilmInsight.

Wraps the LangChain HuggingFaceEmbeddings class so the rest of the pipeline
only needs to call ``EmbeddingGenerator.embed_chunks()``.

The model is loaded once at construction and reused for all subsequent calls,
avoiding repeated model downloads / GPU warm-ups.
"""

from __future__ import annotations

from typing import Any

from ingestion import config
from ingestion.chunker import Chunk
from ingestion.utils import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Generates dense vector embeddings for text chunks.

    Uses ``sentence-transformers/all-MiniLM-L6-v2`` by default (384-dim
    vectors, fast on CPU).  Any HuggingFace sentence-transformer can be
    substituted via ``config.EMBEDDING_MODEL_NAME``.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier.
    device : str
        Compute device — ``"cpu"``, ``"cuda"``, or ``"mps"``.
    batch_size : int
        Number of texts to encode per forward pass.
    """

    def __init__(
        self,
        model_name: str = config.EMBEDDING_MODEL_NAME,
        device: str = config.EMBEDDING_DEVICE,
        batch_size: int = 64,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._embeddings = self._load_model()

    # ── Public API ────────────────────────────────────────────────────────────

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of raw text strings.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.
        """
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        total = len(texts)

        for start in range(0, total, self.batch_size):
            batch = texts[start : start + self.batch_size]
            vectors = self._embeddings.embed_documents(batch)
            all_vectors.extend(vectors)
            logger.info(
                f"  Embedded batch {start + len(batch)}/{total} texts"
            )

        return all_vectors

    def embed_chunks(self, chunks: list[Chunk]) -> list[list[float]]:
        """
        Embed the ``.text`` field of each :class:`~ingestion.chunker.Chunk`.

        Returns vectors in the same order as *chunks*.
        """
        logger.info(f"  Generating embeddings for {len(chunks)} chunks...")
        texts = [chunk.text for chunk in chunks]
        vectors = self.embed_texts(texts)
        logger.info(f"  Embeddings generated: {len(vectors)} vectors")
        return vectors

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string (used for similarity search)."""
        return self._embeddings.embed_query(query)

    @property
    def dimension(self) -> int:
        """Return the embedding dimensionality by encoding a probe string."""
        probe = self._embeddings.embed_query("probe")
        return len(probe)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_model(self) -> Any:
        """
        Instantiate and return a LangChain HuggingFaceEmbeddings object.
        Falls back gracefully if ``langchain-huggingface`` is not installed.
        """
        try:
            from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore[import]
        except ImportError:
            try:
                from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore[no-redef]
            except ImportError as exc:
                raise ImportError(
                    "langchain-huggingface is required. "
                    "Install with: pip install langchain-huggingface"
                ) from exc

        logger.info(
            f"  Loading embedding model: [bold]{self.model_name}[/bold] "
            f"(device={self.device})"
        )
        model = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.device},
            encode_kwargs={"normalize_embeddings": True, "batch_size": self.batch_size},
        )
        logger.info("  Embedding model loaded.")
        return model
