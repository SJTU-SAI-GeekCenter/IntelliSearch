"""Core RAG engine integrating embeddings and document processing.

This module provides the main RAGService class that combines document
processing and vector search capabilities.
"""

import logging
from typing import List, Dict, Any, Optional

from .embeddings import EmbeddingManager
from .documents import DocumentProcessor


class RAGService:
    """Main RAG service for document indexing and search.

    This class integrates document processing and vector embeddings
    to provide a complete RAG (Retrieval-Augmented Generation) solution.

    Attributes:
        embedding_manager: Manages vector embeddings and index
        document_processor: Handles document loading and chunking
        logger: Logging instance
    """

    def __init__(
        self,
        model_path: str,
        index_path: str,
        device: str = "cpu",
        chunk_size: int = 500,
        overlap: int = 50,
        supported_formats: Optional[List[str]] = None,
        auto_load: bool = True,
    ):
        """
        Initialize the RAG service.

        Args:
            model_path: Path to embedding model
            index_path: Path to vector index directory
            device: Device to run model on (cpu, mps, cuda)
            chunk_size: Text chunk size for document splitting
            overlap: Overlap between chunks
            supported_formats: List of supported file extensions
            auto_load: If True, automatically load existing index
        """
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.embedding_manager = EmbeddingManager(
            model_path=model_path,
            index_path=index_path,
            device=device,
            content=True,
        )

        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            overlap=overlap,
            supported_formats=supported_formats,
        )

        # Auto-load existing index if available
        if auto_load and self.embedding_manager.exists():
            self.logger.info("Auto-loading existing index...")
            self.embedding_manager.load()

    def index_directory(
        self, directory_path: str, recursive: bool = True, save: bool = True
    ) -> Dict[str, Any]:
        """
        Index all documents in a directory.

        Args:
            directory_path: Path to the directory
            recursive: If True, process subdirectories recursively
            save: If True, save index after processing

        Returns:
            Dictionary with indexing statistics
        """
        try:
            # Process documents
            chunks = self.document_processor.process_directory(
                directory_path=directory_path,
                recursive=recursive,
            )

            if not chunks:
                self.logger.warning(f"No documents found in {directory_path}")
                return {
                    "status": "warning",
                    "message": "No documents found",
                    "chunks_indexed": 0,
                }

            # Build index
            self.embedding_manager.index(chunks)

            # Save if requested
            if save:
                self.embedding_manager.save()

            return {
                "status": "success",
                "message": f"Successfully indexed {len(chunks)} chunks",
                "chunks_indexed": len(chunks),
                "directory": directory_path,
            }
        except Exception as e:
            self.logger.error(f"Indexing failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "chunks_indexed": 0,
            }

    def index_file(self, file_path: str, save: bool = True) -> Dict[str, Any]:
        """
        Index a single file.

        Args:
            file_path: Path to the file
            save: If True, save index after processing

        Returns:
            Dictionary with indexing statistics
        """
        try:
            # Process document
            chunks = self.document_processor.process_file(file_path)

            if not chunks:
                self.logger.warning(f"No content extracted from {file_path}")
                return {
                    "status": "warning",
                    "message": "No content extracted",
                    "chunks_indexed": 0,
                }

            # Add to index
            self.embedding_manager.upsert(chunks)

            # Save if requested
            if save:
                self.embedding_manager.save()

            return {
                "status": "success",
                "message": f"Successfully indexed {len(chunks)} chunks",
                "chunks_indexed": len(chunks),
                "file": file_path,
            }
        except Exception as e:
            self.logger.error(f"Failed to index {file_path}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "chunks_indexed": 0,
            }

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            Dictionary with search results and metadata
        """
        try:
            results = self.embedding_manager.search(
                query=query,
                limit=limit,
                threshold=threshold,
            )

            return {
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": str(e),
            }

    def delete_documents(self, document_ids: List[str], save: bool = True) -> Dict[str, Any]:
        """
        Delete documents from the index.

        Args:
            document_ids: List of document IDs to delete
            save: If True, save index after deletion

        Returns:
            Dictionary with deletion status
        """
        try:
            # Delete all chunks for each document
            all_chunk_ids = []
            for doc_id in document_ids:
                # Find all chunks for this document
                chunks = self.embedding_manager.search(f"id:{doc_id}", limit=10000)
                chunk_ids = [result.get("id") for result in chunks]
                all_chunk_ids.extend(chunk_ids)

            if all_chunk_ids:
                self.embedding_manager.delete(all_chunk_ids)

                if save:
                    self.embedding_manager.save()

                return {
                    "status": "success",
                    "message": f"Deleted {len(all_chunk_ids)} chunks",
                    "chunks_deleted": len(all_chunk_ids),
                }
            else:
                return {
                    "status": "warning",
                    "message": "No chunks found for the given document IDs",
                    "chunks_deleted": 0,
                }
        except Exception as e:
            self.logger.error(f"Deletion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "chunks_deleted": 0,
            }

    def save_index(self) -> None:
        """Save the vector index to disk."""
        self.embedding_manager.save()

    def load_index(self) -> bool:
        """
        Load the vector index from disk.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        return self.embedding_manager.load()

    def index_exists(self) -> bool:
        """Check if index file exists.

        Returns:
            True if index exists, False otherwise
        """
        return self.embedding_manager.exists()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics
        """
        return {
            "status": "success",
            "index_exists": self.index_exists(),
            "index_path": str(self.embedding_manager.index_path),
            "supported_formats": self.document_processor.supported_formats,
        }
