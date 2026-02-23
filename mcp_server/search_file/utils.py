"""RAG Service Client Utilities.

This module provides utility functions for managing the RAG knowledge base,
including indexing files, managing documents, and handling index operations.
"""

import os
from typing import List, Optional

import httpx


class RAGClient:
    """Client for interacting with the RAG service."""

    def __init__(self, port: Optional[int] = None):
        """
        Initialize RAG service client.

        Args:
            port: RAG service port. Defaults to TOOL_BACKEND_RAG_PORT env var or 39257.
        """
        self.port = port or int(os.environ.get("TOOL_BACKEND_RAG_PORT", 39257))
        self.base_url = f"http://127.0.0.1:{self.port}"

    async def _handle_request_error(self, error: Exception, operation: str) -> dict:
        """
        Handle request errors with consistent error messages.

        Args:
            error: The exception that occurred
            operation: Description of the operation being performed

        Returns:
            Error response dictionary
        """
        if isinstance(error, httpx.ConnectError):
            return {
                "success": False,
                "error": f"Cannot connect to RAG service. Please ensure the service is running on port {self.port}.",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to {operation}: {str(error)}",
            }

    async def search(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> dict:
        """
        Search the RAG knowledge base.

        Args:
            query: Search query string
            limit: Maximum number of results
            threshold: Minimum similarity score

        Returns:
            Search results dictionary
        """
        payload = {"query": query}
        if limit is not None:
            payload["limit"] = limit
        if threshold is not None:
            payload["threshold"] = threshold

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "success":
                    return {
                        "success": True,
                        "results": data.get("results", []),
                        "count": data.get("count", 0),
                    }
                elif data.get("status") == "error":
                    return {
                        "success": False,
                        "error": data.get("error", "Unknown error"),
                        "context": "Search operation",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Unexpected response format: {data}",
                        "context": "Search operation",
                    }

        except httpx.ConnectError as e:
            return await self._handle_request_error(
                e,
                "perform search",
            )
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error {e.response.status_code}: {e.response.text}",
            }
        except Exception as e:
            return await self._handle_request_error(e, "perform search")

    async def index_file(self, file_path: str, save: bool = True) -> dict:
        """
        Index a single file into the RAG knowledge base.

        Args:
            file_path: Path to the file to index
            save: Whether to save the index after adding

        Returns:
            Indexing result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/index/file",
                    params={"file_path": file_path, "save": save},
                    timeout=300.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") in ["success", "warning"]:
                    return {
                        "success": True,
                        **data,
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Unknown indexing error"),
                    }

        except Exception as e:
            return await self._handle_request_error(e, "index file")

    async def index_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        save: bool = True,
    ) -> dict:
        """
        Index all supported documents in a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories
            save: Whether to save the index after indexing

        Returns:
            Indexing result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/index/directory",
                    params={
                        "directory_path": directory_path,
                        "recursive": recursive,
                        "save": save,
                    },
                    timeout=600.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") in ["success", "warning"]:
                    return {
                        "success": True,
                        **data,
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Unknown indexing error"),
                    }

        except Exception as e:
            return await self._handle_request_error(e, "index directory")

    async def delete_documents(self, document_ids: List[str], save: bool = True) -> dict:
        """
        Delete documents from the RAG knowledge base.

        Args:
            document_ids: List of document IDs to delete
            save: Whether to save the index after deletion

        Returns:
            Deletion result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/documents",
                    params={"document_ids": document_ids, "save": save},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") in ["success", "warning"]:
                    return {
                        "success": True,
                        **data,
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Unknown deletion error"),
                    }

        except Exception as e:
            return await self._handle_request_error(e, "delete documents")

    async def get_status(self) -> dict:
        """
        Get RAG service status and statistics.

        Returns:
            Service status dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/status", timeout=10.0)
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    **data,
                }

        except Exception as e:
            return await self._handle_request_error(e, "get status")

    async def save_index(self) -> dict:
        """
        Save the RAG index to disk.

        Returns:
            Save operation result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/index/save", timeout=60.0)
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    **data,
                }

        except Exception as e:
            return await self._handle_request_error(e, "save index")

    async def load_index(self) -> dict:
        """
        Load the RAG index from disk.

        Returns:
            Load operation result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/index/load", timeout=60.0)
                response.raise_for_status()
                data = response.json()

                return {
                    "success": data.get("status") == "success",
                    **data,
                }

        except Exception as e:
            return await self._handle_request_error(e, "load index")


# Global RAG client instance
_rag_client = None


def get_rag_client() -> RAGClient:
    """
    Get or create the global RAG client instance.

    Returns:
        RAGClient instance
    """
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client


async def local_index_file(file_path: str, save: bool = True) -> dict:
    """Index a single file into the RAG knowledge base.

    This tool adds a new document to the search index, making it
    available for semantic search queries. The file content is
    extracted, split into chunks, and vectorized.

    Supported formats:
        - PDF (.pdf): Academic papers, reports, ebooks
        - Text (.txt): Plain text documents
        - Markdown (.md): Documentation, notes
        - Word (.docx): Microsoft Word documents

    When to use:
        - Adding a new document to the knowledge base
        - Updating content after modifying a file
        - Testing document extraction before bulk indexing

    Args:
        file_path (str): Absolute or relative path to the file.
                        Examples:
                          - "./documents/course_syllabus.pdf"
                          - "/path/to/research_paper.pdf"
                          - "notes/introduction_to_ml.md"
        save (bool): Whether to save the index to disk after adding.
                    True (recommended): Preserves the index (default)
                    False: Keeps in memory only (lost on restart)

    Returns:
        dict: Indexing result with structure:
            {
                "success": bool,
                "status": str,          # "success", "warning", "error"
                "message": str,         # Detailed status message
                "chunks_indexed": int,  # Number of chunks created
                "file": str             # File path that was indexed
            }

    Examples:
        >>> # Index a PDF file
        >>> await local_index_file("./papers/attention_is_all_you_need.pdf")

        >>> # Index without saving (for testing)
        >>> await local_index_file("./test.txt", save=False)

    Notes:
        - Large files are split into multiple chunks automatically
        - Each chunk is separately searchable
        - Re-indexing the same file will create duplicate chunks
        - Use local_delete_documents to remove old versions first
    """
    client = get_rag_client()
    return await client.index_file(file_path, save)


async def local_index_directory(
    directory_path: str,
    recursive: bool = True,
    save: bool = True,
) -> dict:
    """Index all supported documents in a directory.

    This tool scans a directory and indexes all supported files
    (PDF, TXT, MD, DOCX), making them searchable. It's the most
    efficient way to build a knowledge base from multiple documents.

    Supported formats:
        - PDF (.pdf): Research papers, reports, books
        - Text (.txt): Plain text documents, code files
        - Markdown (.md): Documentation, notes
        - Word (.docx): Word documents

    When to use:
        - Building a new knowledge base from document collections
        - Adding folders of course materials or papers
        - Bulk indexing documentation directories
        - Setting up search for a project's documentation

    Args:
        directory_path (str): Path to the directory containing documents.
                             Examples:
                               - "./documents"
                               - "/path/to/course_materials"
                               - "./papers/deep_learning"
        recursive (bool): If True, search subdirectories recursively.
                         True (default): Indexes all files in subdirectories
                         False: Only indexes files in the top-level directory
        save (bool): Whether to save the index to disk after indexing.
                    True (recommended): Persists the index (default)
                    False: Keeps in memory only (lost on restart)

    Returns:
        dict: Indexing result with structure:
            {
                "success": bool,
                "status": str,          # "success", "warning", "error"
                "message": str,         # Detailed status message
                "chunks_indexed": int,  # Total number of chunks created
                "directory": str        # Directory that was indexed
            }

    Examples:
        >>> # Index all documents in a folder
        >>> await local_index_directory("./documents")

        >>> # Index only top-level files (no subdirectories)
        >>> await local_index_directory("./papers", recursive=False)

        >>> # Index without saving (for testing)
        >>> await local_index_directory("./test_docs", save=False)

    Notes:
        - Skips unsupported file formats automatically
        - Logs progress for each file processed
        - Large collections may take several minutes
        - Index size depends on total document length
        - Re-indexing creates duplicate chunks (delete old first)
    """
    client = get_rag_client()
    return await client.index_directory(directory_path, recursive, save)


async def local_delete_documents(document_ids: list, save: bool = True) -> dict:
    """Delete documents from the RAG knowledge base.

    This tool removes documents from the search index. Use it to
    clean up outdated content or remove duplicates before re-indexing.

    When to use:
        - Removing outdated documents from the index
        - Cleaning up duplicates before re-indexing
        - Managing knowledge base lifecycle
        - Freeing space by removing unused documents

    Args:
        document_ids (list): List of document IDs to delete.
                            Use base document IDs (without chunk suffix).
                            Examples:
                              - ["document1", "document2"]
                              - ["course_syllabus", "lecture_notes"]
                            Note: Deleting a document removes all its chunks.
        save (bool): Whether to save the index after deletion.
                    True (recommended): Persists changes (default)
                    False: Keeps in memory only (reverted on restart)

    Returns:
        dict: Deletion result with structure:
            {
                "success": bool,
                "status": str,           # "success", "warning", "error"
                "message": str,          # Detailed status message
                "chunks_deleted": int,   # Number of chunks removed
            }

    Examples:
        >>> # Delete a single document
        >>> await local_delete_documents(["old_paper.pdf"])

        >>> # Delete multiple documents
        >>> await local_delete_documents([
        ...     "outdated_syllabus.pdf",
        ...     "old_notes.txt"
        ... ])

    Notes:
        - Document IDs are typically the filename without path/extension
        - All chunks associated with the document are removed
        - Deleted documents cannot be recovered unless re-indexed
        - Use local_search to identify documents before deletion
    """
    client = get_rag_client()
    return await client.delete_documents(document_ids, save)


async def local_get_status() -> dict:
    """Get RAG service status and statistics.

    This tool provides information about the RAG service, including
    whether the index exists, where it's stored, and what formats
    are supported.

    When to use:
        - Checking if the service is running properly
        - Verifying that documents have been indexed
        - Troubleshooting search issues
        - Getting system information for debugging

    Returns:
        dict: Service status with structure:
            {
                "success": bool,
                "status": str,              # "success" or "error"
                "index_exists": bool,       # True if index is loaded
                "index_path": str,          # Path to index file
                "supported_formats": [      # List of supported file types
                    "pdf",
                    "txt",
                    "md",
                    "docx"
                ]
            }

    Examples:
        >>> # Check service status
        >>> await local_get_status()

    Notes:
        - Use this tool to diagnose issues before searching
        - index_exists=False means no documents are indexed yet
        - Use local_index_directory to create an initial index
    """
    client = get_rag_client()
    return await client.get_status()


async def local_save_index() -> dict:
    """Manually save the RAG index to disk.

    This tool persists the current in-memory index to disk.
    The index is automatically saved after most operations, but
    this tool can be used to ensure changes are persisted.

    When to use:
        - Ensuring changes are saved after multiple operations
        - Backing up the index before major changes
        - Manual persistence after disabling auto-save

    Returns:
        dict: Save operation result:
            {
                "success": bool,
                "status": str,      # "success" or "error"
                "message": str      # Status message
            }

    Examples:
        >>> await local_save_index()

    Notes:
        - Most operations save automatically by default
        - Use this if auto-save was disabled
        - Saved indexes persist across service restarts
    """
    client = get_rag_client()
    return await client.save_index()


async def local_load_index() -> dict:
    """Manually load the RAG index from disk.

    This tool loads a previously saved index from disk into memory.
    The index is automatically loaded on service startup, but this
    tool can reload it if needed.

    When to use:
        - Reloading the index after service restart
        - Restoring a previously saved index
        - Troubleshooting index loading issues

    Returns:
        dict: Load operation result:
            {
                "success": bool,
                "status": str,      # "success" or "warning"
                "message": str      # Status message
            }

    Examples:
        >>> await local_load_index()

    Notes:
        - Index is automatically loaded on service startup
        - Returns "warning" if no saved index exists
        - Use local_index_directory to create an initial index
    """
    client = get_rag_client()
    return await client.load_index()
