"""RAG Service - Main entry point for the RAG backend service.

This module provides the FastAPI service for document indexing and search
using the refactored txtai-based RAG system.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uvicorn import run

sys.path.append(os.getcwd())

from core.logger import get_logger
from config.config_loader import Config
from backend.tool_backend.rag_src import RAGService

logger = get_logger("rag_service_backend", "rag_service_backend")
config = Config(config_file_path="config/config.yaml")
config.load_config()
rag_service: Optional[RAGService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app.

    Initializes the RAG service on startup and cleans up on shutdown.
    """
    global rag_service

    logger.info("[RAG Service] Starting up, initializing RAG service...")

    try:
        # Load configuration
        model_path = config.get_with_env(
            "rag.embedding.model_path",
            default="./models/all-MiniLM-L6-v2",
            env_prefix="RAG",
        )
        index_path = config.get_with_env(
            "rag.index.path",
            default="./data/rag_index",
            env_prefix="RAG",
        )
        device = config.get_with_env(
            "rag.embedding.device",
            default="cpu",
            env_prefix="RAG",
        )
        chunk_size = config.get_with_env(
            "rag.documents.chunk_size",
            default=500,
            env_prefix="RAG",
        )
        overlap = config.get_with_env(
            "rag.documents.overlap",
            default=50,
            env_prefix="RAG",
        )
        supported_formats = config.get(
            "rag.documents.supported_formats",
            default=["pdf", "txt", "md", "docx"],
        )

        # Initialize RAG service
        rag_service = RAGService(
            model_path=model_path,
            index_path=index_path,
            device=device,
            chunk_size=chunk_size,
            overlap=overlap,
            supported_formats=supported_formats,
            auto_load=True,
        )

        logger.info("[RAG Service] Service initialized successfully!")

        # Check if initial load directory is configured
        load_dir = config.get("rag.initialization.load_dir")
        if load_dir:
            logger.info(f"[RAG Service] Auto-indexing directory: {load_dir}")
            result = rag_service.index_directory(directory_path=load_dir, recursive=True, save=True)
            if result["status"] == "success":
                logger.info(
                    f"[RAG Service] Auto-indexing completed: {result['chunks_indexed']} chunks"
                )
            elif result["status"] == "warning":
                logger.warning(f"[RAG Service] Auto-indexing warning: {result['message']}")
            else:
                logger.error(f"[RAG Service] Auto-indexing failed: {result.get('message', 'Unknown error')}")

    except Exception as e:
        logger.error(f"[RAG Service] Initialization failed: {e}")
        raise e

    yield

    logger.info("[RAG Service] Service shutdown, cleaning up resources...")
    rag_service = None


# Create FastAPI app
app = FastAPI(
    title="IntelliSearch RAG Service",
    description="Retrieval-Augmented Generation service for document search",
    version="2.0.0",
    lifespan=lifespan,
)


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    limit: Optional[int] = Field(None, description="Maximum number of results")
    threshold: Optional[float] = Field(None, description="Minimum similarity score (0.0-1.0)")


class StatusResponse(BaseModel):
    """Service status response model."""

    status: str
    index_exists: bool
    index_path: str
    supported_formats: list


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get service status and statistics."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    stats = rag_service.get_stats()
    return StatusResponse(**stats)


@app.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    Search for similar documents using semantic search.

    Args:
        request: Search request with query, limit, and threshold

    Returns:
        Search results with scores and content
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Get default search parameters from config
        default_limit = config.get_with_env("rag.search.default_limit", 5, env_prefix="RAG")
        default_threshold = config.get_with_env(
            "rag.search.score_threshold", 0.7, env_prefix="RAG"
        )

        # Use request params or fall back to config defaults
        limit = request.limit or default_limit
        threshold = request.threshold or default_threshold

        result = rag_service.search(
            query=request.query,
            limit=limit,
            threshold=threshold,
        )

        return result
    except Exception as e:
        logger.error(f"[RAG Service] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/file")
async def index_file(file_path: str, save: bool = True):
    """Index a single file.

    Args:
        file_path: Path to the file to index
        save: If True, save index after processing

    Returns:
        Indexing status and statistics
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = rag_service.index_file(file_path=file_path, save=save)
        return result
    except Exception as e:
        logger.error(f"[RAG Service] File indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/directory")
async def index_directory(directory_path: str, recursive: bool = True, save: bool = True):
    """Index all documents in a directory.

    Args:
        directory_path: Path to the directory
        recursive: If True, process subdirectories recursively
        save: If True, save index after processing

    Returns:
        Indexing status and statistics
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = rag_service.index_directory(
            directory_path=directory_path,
            recursive=recursive,
            save=save,
        )
        return result
    except Exception as e:
        logger.error(f"[RAG Service] Directory indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
async def delete_documents(request: dict):
    """Delete documents from the index.

    Args:
        request: Dictionary with document_ids (list) and save (bool)

    Returns:
        Deletion status
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        document_ids = request.get("document_ids", [])
        save = request.get("save", True)

        result = rag_service.delete_documents(document_ids=document_ids, save=save)
        return result
    except Exception as e:
        logger.error(f"[RAG Service] Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/save")
async def save_index():
    """Manually save the vector index."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        rag_service.save_index()
        return {"status": "success", "message": "Index saved successfully"}
    except Exception as e:
        logger.error(f"[RAG Service] Index save failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/load")
async def load_index():
    """Manually load the vector index."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        success = rag_service.load_index()
        if success:
            return {"status": "success", "message": "Index loaded successfully"}
        else:
            return {
                "status": "warning",
                "message": "Index file not found, starting with empty index",
            }
    except Exception as e:
        logger.error(f"[RAG Service] Index load failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/load_dir")
async def get_load_dir():
    """Get the configured load directory path."""
    load_dir = config.get("rag.initialization.load_dir")
    if not load_dir:
        return {"success": True, "load_dir": None, "message": "No load directory configured"}
    return {"success": True, "load_dir": load_dir}


@app.get("/files/tree")
async def get_file_tree(path: Optional[str] = None):
    """Get the file tree structure of the load directory.

    Args:
        path: Relative path within load directory. If None, returns root tree.

    Returns:
        File tree structure with directories and files
    """
    load_dir = config.get("rag.initialization.load_dir")
    if not load_dir:
        raise HTTPException(status_code=404, detail="No load directory configured")

    try:
        # Construct full path
        if path:
            full_path = os.path.join(load_dir, path)
            rel_path = path
        else:
            full_path = load_dir
            rel_path = ""

        # Validate path is within load_dir
        full_path = os.path.abspath(full_path)
        load_dir_abs = os.path.abspath(load_dir)
        if not full_path.startswith(load_dir_abs):
            raise HTTPException(status_code=403, detail="Access denied: path outside load directory")

        # Check if path exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Path not found")

        # Build tree structure
        tree = {"type": "directory", "name": os.path.basename(full_path), "path": rel_path, "children": []}

        if os.path.isdir(full_path):
            try:
                for item in sorted(os.listdir(full_path)):
                    item_path = os.path.join(full_path, item)
                    item_rel_path = os.path.join(rel_path, item) if rel_path else item

                    if os.path.isdir(item_path):
                        tree["children"].append({
                            "type": "directory",
                            "name": item,
                            "path": item_rel_path,
                        })
                    elif os.path.isfile(item_path):
                        # Get file extension
                        _, ext = os.path.splitext(item)
                        tree["children"].append({
                            "type": "file",
                            "name": item,
                            "path": item_rel_path,
                            "extension": ext.lstrip('.'),
                        })
            except PermissionError:
                logger.warning(f"Permission denied accessing: {full_path}")
                tree["error"] = "Permission denied"

        return {"success": True, "tree": tree}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG Service] Failed to get file tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/search")
async def search_files(
    query: str,
    search_filename: bool = False,
    search_content: bool = False,
):
    """Search for files by name or content within load directory.

    Args:
        query: Search query string
        search_filename: If True, search in filenames
        search_content: If True, search within file contents

    Returns:
        List of matching files with context
    """
    load_dir = config.get("rag.initialization.load_dir")
    if not load_dir:
        raise HTTPException(status_code=404, detail="No load directory configured")

    try:
        load_dir_abs = os.path.abspath(load_dir)
        results = []

        for root, dirs, files in os.walk(load_dir_abs):
            for filename in files:
                filepath = os.path.join(root, filename)

                # Get relative path
                rel_path = os.path.relpath(filepath, load_dir_abs)

                # Filename search
                if search_filename and query.lower() in filename.lower():
                    results.append({
                        "type": "filename_match",
                        "path": rel_path,
                        "name": filename,
                    })
                    # Don't continue - also check content if both flags are True

                # Content search
                if search_content:
                    try:
                        # Only search text-based files
                        _, ext = os.path.splitext(filename)
                        if ext.lower() in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css', '.sh', '.bash']:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if query.lower() in line.lower():
                                        # Find keyword position for context extraction
                                        keyword_pos = line.lower().find(query.lower())
                                        line_stripped = line.strip()

                                        # Extract context: 300 chars before + 300 chars after keyword
                                        context_start = max(0, keyword_pos - 300)
                                        context_end = min(len(line_stripped), keyword_pos + len(query) + 300)

                                        # Add ellipsis if truncated
                                        preview = line_stripped[context_start:context_end]
                                        if context_start > 0:
                                            preview = "..." + preview
                                        if context_end < len(line_stripped):
                                            preview = preview + "..."

                                        results.append({
                                            "type": "content_match",
                                            "path": rel_path,
                                            "name": filename,
                                            "line_number": line_num,
                                            "preview": preview,
                                        })
                                        break  # Only show first match per file
                    except (PermissionError, UnicodeDecodeError):
                        pass

        return {"success": True, "query": query, "results": results}
    except Exception as e:
        logger.error(f"[RAG Service] File search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/content")
async def get_file_content(path: str, line_start: Optional[int] = None, line_end: Optional[int] = None):
    """Get content of a specific file within load directory.

    Args:
        path: Relative path to file within load directory
        line_start: Optional start line number (1-indexed)
        line_end: Optional end line number (1-indexed)

    Returns:
        File content with metadata
    """
    load_dir = config.get("rag.initialization.load_dir")
    if not load_dir:
        raise HTTPException(status_code=404, detail="No load directory configured")

    try:
        # Construct and validate full path
        full_path = os.path.abspath(os.path.join(load_dir, path))
        load_dir_abs = os.path.abspath(load_dir)

        if not full_path.startswith(load_dir_abs):
            raise HTTPException(status_code=403, detail="Access denied: path outside load directory")

        if not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(full_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()

        total_lines = len(lines)

        # Apply line range filter
        if line_start is not None:
            if line_start < 1 or line_start > total_lines:
                raise HTTPException(status_code=400, detail=f"Invalid line_start: {line_start}")
            start_idx = line_start - 1
        else:
            start_idx = 0

        if line_end is not None:
            if line_end < line_start or line_end > total_lines:
                raise HTTPException(status_code=400, detail=f"Invalid line_end: {line_end}")
            end_idx = line_end
        else:
            end_idx = total_lines

        selected_lines = lines[start_idx:end_idx]
        content = ''.join(selected_lines)

        return {
            "success": True,
            "path": path,
            "total_lines": total_lines,
            "line_start": line_start or 1,
            "line_end": line_end or total_lines,
            "content": content,
            "line_count": len(selected_lines),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG Service] Failed to get file content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/markdown/structure")
async def get_markdown_structure(path: str):
    """Analyze markdown file structure (headings and line count).

    Args:
        path: Relative path to markdown file within load directory

    Returns:
        Markdown structure with headings hierarchy and statistics
    """
    load_dir = config.get("rag.initialization.load_dir")
    if not load_dir:
        raise HTTPException(status_code=404, detail="No load directory configured")

    try:
        # Construct and validate full path
        full_path = os.path.abspath(os.path.join(load_dir, path))
        load_dir_abs = os.path.abspath(load_dir)

        if not full_path.startswith(load_dir_abs):
            raise HTTPException(status_code=403, detail="Access denied: path outside load directory")

        if not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="File not found")

        _, ext = os.path.splitext(full_path)
        if ext.lower() != '.md':
            raise HTTPException(status_code=400, detail="File is not a markdown file")

        # Parse markdown structure
        headings = []
        total_lines = 0
        code_blocks = 0

        with open(full_path, 'r', encoding='utf-8') as f:
            in_code_block = False
            for line_num, line in enumerate(f, 1):
                total_lines += 1

                # Track code blocks
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    if in_code_block:
                        code_blocks += 1

                # Extract headings (not in code blocks)
                if not in_code_block and line.startswith('#'):
                    # Count heading level
                    level = 0
                    for char in line:
                        if char == '#':
                            level += 1
                        else:
                            break

                    # Extract heading text
                    text = line[level:].strip()

                    headings.append({
                        "level": level,
                        "text": text,
                        "line_number": line_num,
                    })

        return {
            "success": True,
            "path": path,
            "total_lines": total_lines,
            "heading_count": len(headings),
            "code_block_count": code_blocks,
            "headings": headings,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG Service] Failed to analyze markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Get port from configuration with environment variable override support
    # Override via: TOOL_BACKEND_RAG_PORT
    port = config.get_with_env("tool_backend.rag_port", 39257)
    print(f"[RAG Service] Starting RAG Service on port {port}")
    run(app, host="0.0.0.0", port=port, log_level="info")
