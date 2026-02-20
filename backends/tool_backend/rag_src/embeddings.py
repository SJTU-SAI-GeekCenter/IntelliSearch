"""Embeddings module for vector storage and retrieval using txtai.

This module provides a wrapper around txtai's Embeddings class to handle
vector indexing, search, and persistence operations.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from txtai.embeddings import Embeddings


class EmbeddingManager:
    """Manage vector embeddings and index operations using txtai.

    This class provides methods to create, load, and query vector indices
    using txtai's embedding model. It supports persistence and incremental updates.

    Attributes:
        embeddings: txtai Embeddings instance
        index_path: Path to save/load the index
        logger: Logging instance
    """

    def __init__(
        self,
        model_path: str,
        index_path: str,
        device: str = "cpu",
        content: bool = True,
    ):
        """
        Initialize the EmbeddingManager.

        Args:
            model_path: Path or HuggingFace model ID for embedding model
            index_path: Directory path to store/load the vector index
            device: Device to run model on (cpu, mps, cuda)
            content: Whether to store original content in index
        """
        self.index_path = Path(index_path)
        self.content = content
        self.logger = logging.getLogger(__name__)

        # Convert model path to absolute path if it's a local path
        model_path = self._resolve_model_path(model_path)

        # Initialize txtai Embeddings
        self.embeddings = Embeddings(
            path=model_path,
            content=content,
            device=device,
        )

        self._loaded = False

    def _resolve_model_path(self, model_path: str) -> str:
        """
        Resolve model path to absolute path or HuggingFace ID.

        Args:
            model_path: Original model path

        Returns:
            Resolved absolute path or original HuggingFace ID
        """
        # If it's already a HuggingFace model ID (contains / but not starting with . or /)
        if "/" in model_path and not model_path.startswith((".", "/")):
            return model_path

        # Convert to absolute path
        if not os.path.isabs(model_path):
            model_path = os.path.abspath(model_path)

        # Check if path exists
        if not os.path.exists(model_path):
            self.logger.warning(
                f"Model path does not exist: {model_path}. "
                "Falling back to HuggingFace model ID: sentence-transformers/all-MiniLM-L6-v2"
            )
            return "sentence-transformers/all-MiniLM-L6-v2"

        return model_path

    def index(self, documents: List[Tuple[str, str, Any]]) -> None:
        """
        Build vector index from documents.

        Args:
            documents: List of tuples (id, text, tags_or_None)
                      Example: [("doc1", "text content", None), ...]

        Note:
            This will rebuild the entire index. For incremental updates,
            use upsert() or delete().
        """
        try:
            self.embeddings.index(documents)
            self._loaded = True
            self.logger.info(f"Indexed {len(documents)} documents")
        except Exception as e:
            self.logger.error(f"Failed to index documents: {e}")
            raise

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            List of search results with keys: id, score, text (if content=True)
        """
        if not self._loaded:
            self.logger.warning("Index not loaded, attempting to load from disk")
            self.load()

        try:
            # txtai search parameters
            search_params = {}
            if limit is not None:
                search_params["limit"] = limit

            results = self.embeddings.search(query, **search_params)

            # Apply threshold filtering manually if specified
            if threshold is not None:
                results = [r for r in results if r.get("score", 0) >= threshold]

            return results
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def upsert(self, documents: List[Tuple[str, str, Any]]) -> None:
        """
        Insert or update documents in the index.

        Args:
            documents: List of tuples (id, text, tags_or_None)
        """
        try:
            self.embeddings.upsert(documents)
            self.logger.info(f"Upserted {len(documents)} documents")
        except Exception as e:
            self.logger.error(f"Failed to upsert documents: {e}")
            raise

    def delete(self, ids: List[str]) -> None:
        """
        Delete documents from the index.

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.embeddings.delete(ids)
            self.logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            raise

    def save(self) -> None:
        """Save the vector index to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.embeddings.save(str(self.index_path))
            self.logger.info(f"Index saved to {self.index_path}")
        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")
            raise

    def load(self) -> bool:
        """
        Load vector index from disk.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        if not self.index_path.exists():
            self.logger.warning(f"Index file not found at {self.index_path}")
            return False

        try:
            self.embeddings.load(str(self.index_path))
            self._loaded = True
            self.logger.info(f"Index loaded from {self.index_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load index: {e}")
            return False

    def exists(self) -> bool:
        """Check if index file exists on disk.

        Returns:
            True if index exists, False otherwise
        """
        return self.index_path.exists()
