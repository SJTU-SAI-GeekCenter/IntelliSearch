"""RAG (Retrieval-Augmented Generation) Service.

A high-performance document search service using txtai for embeddings
and semantic search.

Main Components:
    - RAGService: Core service for document indexing and search
    - EmbeddingManager: Vector storage and retrieval
    - DocumentProcessor: Document loading and chunking

Example:
    >>> from backend.tool_backend.rag_src import RAGService
    >>>
    >>> # Initialize service
    >>> service = RAGService(
    ...     model_path="./models/all-MiniLM-L6-v2",
    ...     index_path="./data/rag_index"
    ... )
    >>>
    >>> # Index documents
    >>> service.index_directory("./documents")
    >>>
    >>> # Search
    >>> results = service.search("What is RAG?")
"""

from .core import RAGService
from .embeddings import EmbeddingManager
from .documents import DocumentProcessor

__all__ = [
    "RAGService",
    "EmbeddingManager",
    "DocumentProcessor",
]

__version__ = "2.0.0"
