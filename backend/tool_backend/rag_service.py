"""RAG Service - Main entry point for the RAG backend service.

This module provides the FastAPI service for document indexing and search
using the refactored txtai-based RAG system.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uvicorn import run

sys.path.append(os.getcwd())

from core.logger import get_logger
from config.config_loader import Config
from backend.tool_backend.rag_src import RAGService

logger = get_logger(__name__)
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


if __name__ == "__main__":
    # Get port from configuration with environment variable override support
    # Override via: TOOL_BACKEND_RAG_PORT
    port = config.get_with_env("tool_backend.rag_port", 39257)
    print(f"[RAG Service] Starting RAG Service on port {port}")
    run(app, host="0.0.0.0", port=port, log_level="info")
