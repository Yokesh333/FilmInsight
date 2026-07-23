import logging
import threading

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Singleton service to lazily load and cache the HuggingFace embedding model.
    Ensures the model is loaded only once when first requested.
    """

    _embedder = None
    _lock = threading.Lock()

    @classmethod
    def get_embedder(cls):
        if cls._embedder is None:
            with cls._lock:
                if cls._embedder is None:
                    import psutil

                    process = psutil.Process()
                    mem_before = process.memory_info().rss / (1024 * 1024)

                    logger.info(
                        f"[EmbeddingService] Lazy loading HuggingFace embedding model..."
                        f" (RAM: {mem_before:.1f} MB)"
                    )

                    try:
                        logger.info(
                            "[EmbeddingService] Importing HuggingFaceEmbeddings..."
                        )

                        try:
                            from langchain_huggingface import HuggingFaceEmbeddings
                            logger.info(
                                "[EmbeddingService] Using langchain_huggingface package."
                            )
                        except ImportError:
                            logger.warning(
                                "[EmbeddingService] langchain_huggingface not found. "
                                "Falling back to langchain.embeddings."
                            )
                            from langchain.embeddings import HuggingFaceEmbeddings

                        from app.core.config import get_settings

                        settings = get_settings()

                        model = getattr(
                            settings,
                            "EMBEDDING_MODEL_NAME",
                            "sentence-transformers/all-MiniLM-L6-v2",
                        )

                        device = getattr(settings, "EMBEDDING_DEVICE", "cpu")

                        logger.info(
                            f"[EmbeddingService] Model: {model}"
                        )
                        logger.info(
                            f"[EmbeddingService] Device: {device}"
                        )

                        logger.info(
                            "[EmbeddingService] Creating HuggingFaceEmbeddings instance..."
                        )

                        logger.info("STEP 1 - Before HuggingFaceEmbeddings")

                        cls._embedder = HuggingFaceEmbeddings(
                            model_name=model,
                            model_kwargs={
                                "device": device,
                            },
                            encode_kwargs={
                                "normalize_embeddings": True,
                            },
                        )

                        logger.info("STEP 2 - HuggingFaceEmbeddings created")

                        logger.info(
                            "[EmbeddingService] HuggingFaceEmbeddings instance created successfully."
                        )

                        mem_after = process.memory_info().rss / (1024 * 1024)

                        logger.info(
                            "[EmbeddingService] Embedding model loaded successfully."
                        )
                        logger.info(
                            f"[EmbeddingService] RAM Before: {mem_before:.1f} MB"
                        )
                        logger.info(
                            f"[EmbeddingService] RAM After : {mem_after:.1f} MB"
                        )
                        logger.info(
                            f"[EmbeddingService] RAM Used  : {mem_after - mem_before:.1f} MB"
                        )

                    except Exception as e:
                        logger.exception(
                            f"[EmbeddingService] Failed to initialize embedding model: {e}"
                        )
                        raise

        else:
            logger.info(
                "[EmbeddingService] Reusing cached embedding model."
            )

        return cls._embedder


def get_embedder():
    """
    Returns the cached HuggingFaceEmbeddings singleton instance.
    """
    return EmbeddingService.get_embedder()