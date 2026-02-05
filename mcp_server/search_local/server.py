"""Local RAG Search MCP Server.

This server provides MCP tools for searching local document collections
using the RAG (Retrieval-Augmented Generation) service.

The RAG service indexes documents (PDF, TXT, MD, DOCX) and provides
semantic search capabilities using txtai embeddings.
"""

import os
import httpx
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Local-RAG-Search")

# RAG service configuration
PORT = int(os.environ.get("TOOL_BACKEND_RAG_PORT", 39257))
BASE_URL = f"http://127.0.0.1:{PORT}"


def handle_response(data: dict, error_context: str) -> dict:
    """
    Handle RAG service response with proper error handling.

    Args:
        data: Response data from RAG service
        error_context: Context description for error messages

    Returns:
        Formatted response dictionary
    """
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
            "context": error_context,
        }
    else:
        return {
            "success": False,
            "error": f"Unexpected response format: {data}",
            "context": error_context,
        }


@mcp.tool()
async def local_search(
    query: str,
    limit: Optional[int] = None,
    threshold: Optional[float] = None,
):
    """Search local document collection using semantic search.

    This tool performs semantic search on indexed documents including
    PDFs, text files, markdown files, and Word documents. It uses
    vector embeddings to find the most relevant content based on
    meaning rather than keyword matching.

    When to use:
        - User asks about specific information in local documents
        - Questions about course materials, research papers, documentation
        - Retrieving facts from uploaded PDF/TXT/MD files
        - Finding relevant passages from a knowledge base

    Features:
        - Semantic understanding: Finds content by meaning, not just keywords
        - Multi-format support: Works with PDF, TXT, MD, DOCX files
        - Relevance scoring: Returns results with similarity scores
        - Configurable precision: Adjust threshold and result count

    Args:
        query (str): The search query or question.
                     Examples:
                       - "What is machine learning?"
                       - "Explain the neural network architecture"
                       - "Find information about course prerequisites"
        limit (int, optional): Maximum number of results to return.
                              If not specified, uses server default (usually 5).
                              Recommended range: 3-10 for focused results.
        threshold (float, optional): Minimum similarity score (0.0 to 1.0).
                                    Higher values = more precise but fewer results.
                                    - 0.9-1.0: Very strict, only exact matches
                                    - 0.7-0.9: Good balance (recommended)
                                    - 0.5-0.7: More inclusive, may include noise
                                    - 0.3-0.5: Very permissive, broad search
                                    If not specified, uses server default (0.7).

    Returns:
        dict: Search results with the following structure:
            {
                "success": bool,  # True if search succeeded
                "results": [     # List of search results
                    {
                        "id": str,           # Document chunk ID
                        "score": float,      # Similarity score (0-1)
                        "text": str          # Matched text content
                    },
                    ...
                ],
                "count": int,      # Number of results returned
                "error": str       # Error message if success=False
            }

    Examples:
        >>> # Basic search
        >>> await local_search("What are the prerequisites?")

        >>> # Search with custom parameters
        >>> await local_search(
        ...     query="deep learning architectures",
        ...     limit=10,
        ...     threshold=0.8
        ... )

    Notes:
        - The RAG service must be running before using this tool
        - Documents must be indexed before they can be searched
        - Use local_index_directory or local_index_file to add documents
    """
    # Build request payload
    payload = {"query": query}
    if limit is not None:
        payload["limit"] = limit
    if threshold is not None:
        payload["threshold"] = threshold

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return handle_response(data, "Search operation")

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to RAG service. Please ensure the service is running on port "
            f"{PORT}. Start it with: python backend/tool_backend/rag_service.py",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during search: {str(e)}",
        }


@mcp.tool()
async def local_index_file(file_path: str, save: bool = True):
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/index/file",
                params={"file_path": file_path, "save": save},
                timeout=300.0,  # Longer timeout for indexing
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

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to RAG service. Please ensure the service is running on port "
            f"{PORT}.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to index file: {str(e)}",
        }


@mcp.tool()
async def local_index_directory(
    directory_path: str,
    recursive: bool = True,
    save: bool = True,
):
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/index/directory",
                params={
                    "directory_path": directory_path,
                    "recursive": recursive,
                    "save": save,
                },
                timeout=600.0,  # Extended timeout for large directories
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

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to RAG service. Please ensure the service is running on port "
            f"{PORT}.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to index directory: {str(e)}",
        }


@mcp.tool()
async def local_delete_documents(document_ids: List[str], save: bool = True):
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}/documents",
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

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to RAG service. Please ensure the service is running on port "
            f"{PORT}.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete documents: {str(e)}",
        }


@mcp.tool()
async def local_get_status():
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/status", timeout=10.0)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                **data,
            }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to RAG service. Please ensure the service is running on port "
            f"{PORT}.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get status: {str(e)}",
        }


@mcp.tool()
async def local_save_index():
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/index/save", timeout=60.0)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                **data,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save index: {str(e)}",
        }


@mcp.tool()
async def local_load_index():
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/index/load", timeout=60.0)
            response.raise_for_status()
            data = response.json()

            return {
                "success": data.get("status") == "success",
                **data,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load index: {str(e)}",
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
