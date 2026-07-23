import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Singleton service to lazily load and cache the HuggingFace embedding model.
    Ensures the model is loaded only once when first requested.
    """
    _embedder = None
    import threading
    _lock = threading.Lock()

    @classmethod
    def get_embedder(cls):
        if cls._embedder is None:
            with cls._lock:
                if cls._embedder is None:
                    import psutil
                    process = psutil.Process()
                    mem_before = process.memory_info().rss / (1024 * 1024)
                    
                    logger.info(f"[EmbeddingService] Lazy loading HuggingFace embedding model... (RAM: {mem_before:.1f} MB)")
                    try:
                        from langchain_huggingface import HuggingFaceEmbeddings
                    except ImportError:
                        from langchain.embeddings import HuggingFaceEmbeddings

                    from app.core.config import get_settings
                    s = get_settings()
                    model = getattr(s, "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
                    device = getattr(s, "EMBEDDING_DEVICE", "cpu")

                    logger.info(f"[EmbeddingService] Initialising model: {model} on device: {device}")
                    cls._embedder = HuggingFaceEmbeddings(
                        model_name=model,
                        model_kwargs={"device": device},
                        encode_kwargs={"normalize_embeddings": True},
                    )
                    
                    mem_after = process.memory_info().rss / (1024 * 1024)
                    logger.info(f"[EmbeddingService] Embedding model loaded successfully and cached. (RAM: {mem_after:.1f} MB | Diff: {mem_after - mem_before:.1f} MB)")
        
        return cls._embedder

def get_embedder():
    """Returns the cached HuggingFaceEmbeddings singleton instance."""
    return EmbeddingService.get_embedder()
