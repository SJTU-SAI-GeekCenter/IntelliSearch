"""Local RAG Search MCP Server.

This server provides MCP tools for searching local document collections
using the RAG (Retrieval-Augmented Generation) service.

The RAG service indexes documents (PDF, TXT, MD, DOCX) and provides
semantic search capabilities using txtai embeddings.
"""

import os
import httpx
import seedir

from typing import Optional
from mcp.server.fastmcp import FastMCP
from utils import get_rag_client

# Initialize FastMCP server
mcp = FastMCP("Local-RAG-Search")
PORT = int(os.environ.get("TOOL_BACKEND_RAG_PORT", 39257))
BASE_URL = f"http://127.0.0.1:{PORT}"


async def _rag_get_request(endpoint: str, params: dict = None) -> dict:
    """
    Helper function for making GET requests to RAG service.

    Args:
        endpoint: API endpoint path
        params: Query parameters

    Returns:
        Response data or error dictionary
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}{endpoint}",
                params=params or {},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot connect to RAG service on port {PORT}. "
            f"Start it with: python backend/tool_backend/rag_service.py",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# semantic search based on RAG
@mcp.tool()
async def search_semantic(
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
        - Use utils.local_index_directory or utils.local_index_file to add documents
    """
    client = get_rag_client()

    # Enhance error message for search
    result = await client.search(query, limit, threshold)

    if not result.get("success") and "Cannot connect" in result.get("error", ""):
        result["error"] += f" Start it with: python backend/tool_backend/rag_service.py"

    return result


# Precise search tools
@mcp.tool()
async def browse_file_tree(path: Optional[str] = None, depth: Optional[int | str] = 1):
    """Browse the file tree structure of RAG load directory.

    This tool allows you to explore the directory structure of the
    configured RAG load directory, viewing both files and subdirectories
    in a human-readable tree format using the seedir library.

    When to use:
        - Exploring the document collection structure
        - Finding files before performing precise search
        - Understanding how documents are organized
        - Navigating to specific directories for further operations

    Args:
        path (str, optional): Relative path within load directory.
                             If None, returns the root directory tree.
                             Examples:
                               - None: Browse root directory
                               - "documents": Browse documents subdirectory
                               - "papers/ml": Browse nested directory

        depth (int | str, optional): Tree depth limit.
                                    - Integer (1, 2, 3...): Show specific depth level
                                    - "all": Show entire tree recursively (use with caution!)
                                    - Default: 1 (immediate children only, non-recursive)
                                    Examples:
                                      - 1: Show only direct children
                                      - 2: Show children + grandchildren
                                      - "all": Show full recursive tree (can be large!)

    Returns:
        dict: Tree structure with format:
            {
                "success": bool,
                "path": str,              # Current path
                "tree": str,              # Human-readable tree string
                "item_count": int,        # Total number of items
                "folder_count": int,      # Number of folders
                "file_count": int         # Number of files
            }

    Examples:
        >>> # Browse root directory (depth=1, non-recursive)
        >>> await browse_file_tree()

        >>> # Browse specific subdirectory with depth limit
        >>> await browse_file_tree("上海交通大学 新生指南", depth=2)

        >>> # Browse entire tree recursively (use with caution!)
        >>> await browse_file_tree("上海交通大学 新生指南", depth="all")

    Performance Notes:
        - depth=1 (default): Fast, recommended for initial exploration
        - depth=2-3: Moderate speed, good for structured directories
        - depth="all": Can be slow for large directories, use selectively

    Notes:
        - Uses seedir library for tree formatting
        - Lines style (| and └──) for clear hierarchy visualization
        - Paths are relative to load directory
        - Cannot access files outside load directory
    """
    # First get the load_dir from RAG service
    config_result = await _rag_get_request("/config/load_dir", {})
    if not config_result.get("success"):
        return config_result

    load_dir = config_result.get("load_dir")
    if not load_dir:
        return {"success": False, "error": "No load directory configured"}

    # Construct full path
    if path:
        full_path = os.path.join(load_dir, path)
    else:
        full_path = load_dir

    # Security check: ensure path is within load_dir
    full_path = os.path.abspath(full_path)
    load_dir_abs = os.path.abspath(load_dir)
    if not full_path.startswith(load_dir_abs):
        return {
            "success": False,
            "error": "Access denied: path outside load directory",
        }

    # Check if path exists
    if not os.path.exists(full_path):
        return {"success": False, "error": f"Path not found: {path}"}

    try:
        if depth == "all":
            tree_string = seedir.seedir(
                full_path, style="lines", printout=False, indent=4
            )
        else:
            tree_string = seedir.seedir(
                full_path, style="lines", depthlimit=depth, printout=False, indent=4
            )

        # Count items
        if os.path.isdir(full_path):
            items = os.listdir(full_path)
            folder_count = len(
                [i for i in items if os.path.isdir(os.path.join(full_path, i))]
            )
            file_count = len(
                [i for i in items if os.path.isfile(os.path.join(full_path, i))]
            )
            item_count = len(items)
        else:
            folder_count = 0
            file_count = 1
            item_count = 1

        return {
            "success": True,
            "path": path or "/",
            "tree": tree_string,
            "item_count": item_count,
            "folder_count": folder_count,
            "file_count": file_count,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate tree: {str(e)}",
        }


@mcp.tool()
async def search_files_precise(
    query: str,
    search_filename: bool = False,
    search_content: bool = False,
):
    """Search for files by filename or content within RAG load directory.

    This tool performs precise text-based search for files, either
    matching filenames or searching within file contents. Unlike
    semantic search, this finds exact text matches.

    When to use:
        - Finding files with specific names or patterns
        - Searching for exact text within documents
        - Locating files containing specific keywords
        - Complementing semantic search with precise matching

    Args:
        query (str): Search query string for exact matching.
                    Examples:
                      - "README": Find files with "README" in name
                      - "import numpy": Find code with this import
        search_filename (bool): If True, search in filenames.
                               If False, skip filename search.
                               False (default): Don't search filenames
        search_content (bool): If True, search within file contents.
                              If False, skip content search.
                              False (default): Don't search file contents

    Returns:
        dict: Optimized search results:
            {
                "success": bool,
                "query": str,
                "match_count": int,          # Total number of matches
                "results": [
                    {
                        "type": "filename_match" | "content_match",
                        "location": str,        # "path/to/file.txt (line 123)"
                        "preview": str          # Context preview around match
                    },
                    ...
                ]
            }

    Examples:
        >>> # Search for README files (by filename)
        >>> await search_files_precise("README", search_filename=True)

        >>> # Search for files containing "API endpoint"
        >>> await search_files_precise("API endpoint", search_content=True)

        >>> # Search both filename and content
        >>> await search_files_precise("config", search_filename=True, search_content=True)

    Preview Format:
        - For filename matches: Shows the filename path
        - For content matches: Shows 300 chars before + 300 chars after the keyword

    Validation:
        - At least one of search_filename or search_content must be True
        - Returns error if both are False

    Notes:
        - Content search only works with text-based files (.txt, .md, .py, etc.)
        - Case-insensitive matching
        - Returns first match per file for content search
        - Only searches within load directory
        - Preview provides context around the matched keyword
    """
    # Validate at least one search option is enabled
    if not search_filename and not search_content:
        return {
            "success": False,
            "error": "At least one search option must be enabled. Please set search_filename=True or search_content=True (or both).",
        }

    # Make request with both flags
    result = await _rag_get_request(
        "/files/search",
        {
            "query": query,
            "search_filename": search_filename,
            "search_content": search_content,
        },
    )

    if not result.get("success"):
        return result

    # Extract and optimize results
    raw_results = result.get("results", [])
    optimized_results = []

    for item in raw_results:
        match_type = item.get("type", "unknown")
        path = item.get("path", "")
        name = item.get("name", "")
        line_number = item.get("line_number")
        preview = item.get("preview", "")

        # Build formatted location string
        if match_type == "content_match" and line_number is not None:
            location = f"{path} (line {line_number})"
        else:
            location = path

        # For content matches, enhance preview with context
        if match_type == "content_match" and preview:
            pass
        elif match_type == "filename_match":
            # For filename matches, preview is just the filename
            preview = f"Filename match: {name}"

        optimized_results.append(
            {
                "type": match_type,
                "location": location,
                "preview": preview,
            }
        )

    return {
        "success": True,
        "query": query,
        "match_count": len(optimized_results),
        "results": optimized_results,
    }


@mcp.tool()
async def get_file_content(
    path: str, line_start: Optional[int] = None, line_end: Optional[int] = None
):
    """Get content of a specific file with optional line range.

    This tool retrieves the actual content of a file from the RAG
    load directory, with support for reading specific line ranges
    and intelligent validation.

    When to use:
        - Reading the full content of a document
        - Extracting specific sections by line numbers
        - Reviewing code or configuration files
        - Getting precise content after browsing/searching

    Args:
        path (str): Relative path to file within load directory.
                   Examples:
                     - "README.md"
                     - "documents/course_syllabus.pdf"
                     - "config/settings.yaml"
        line_start (int, optional): Start line number (1-indexed).
                                   If None, starts from line 1.
                                   Must be >= 1.
        line_end (int, optional): End line number (1-indexed).
                                 If None, reads to end of file.
                                 Must be >= line_start if specified.
                                 Auto-adjusted if exceeds total lines.

    Returns:
        dict: Optimized file content structure:
            {
                "success": bool,
                "path": str,
                "total_line_index": str,     # Format: "1-max_line"
                "selected_line_index": str,  # Format: "start-end"
                "content": str,              # File content
            }

    Examples:
        >>> # Read entire file
        >>> await get_file_content("README.md")
        # Returns: {"total_line_index": "1-150", "selected_line_index": "1-150", ...}

        >>> # Read lines 10-20
        >>> await get_file_content("main.py", line_start=10, line_end=20)
        # Returns: {"total_line_index": "1-100", "selected_line_index": "10-20", ...}

        >>> # Read from line 50 to end (file has 120 lines)
        >>> await get_file_content("logs.txt", line_start=50)
        # Returns: {"selected_line_index": "50-120", "note": "Reading from line 50 to end...", ...}

        >>> # Request beyond file length (auto-adjusted)
        >>> await get_file_content("doc.md", line_start=100, line_end=200)  # file has 150 lines
        # Returns: {"selected_line_index": "100-150", "note": "Requested line_end (200) exceeded...", ...}

    Validation Rules:
        - line_start must be >= 1 (returns error if invalid)
        - line_end must be >= line_start (returns error if invalid)
        - If line_end > total_lines: auto-adjusted to total_lines (no error)
        - If line_start > total_lines: returns error from backend

    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - Auto-adjustment is silent but noted in response
        - Use get_markdown_structure to find line numbers before reading
    """
    # Validate line_start (must be positive integer)
    if line_start is not None and line_start < 1:
        return {
            "success": False,
            "error": f"Invalid line_start: {line_start}. Must be >= 1 (line numbers are 1-indexed).",
        }

    # Validate line_end (must be >= line_start if both specified)
    if line_end is not None and line_start is not None and line_end < line_start:
        return {
            "success": False,
            "error": f"Invalid line_end: {line_end}. Must be >= line_start ({line_start}).",
        }

    # First, get file total lines by fetching the full file
    initial_params = {"path": path}
    initial_result = await _rag_get_request("/files/content", initial_params)

    if not initial_result.get("success"):
        return initial_result

    total_lines = initial_result.get("total_lines", 0)
    full_content = initial_result.get("content", "")
    original_line_end = line_end

    # Pre-adjust line_end if it exceeds total lines
    if line_end is not None and line_end > total_lines:
        line_end = total_lines  # Auto-adjust to max line

    # Determine actual line range
    actual_start = line_start if line_start is not None else 1
    actual_end = line_end if line_end is not None else total_lines

    # If requesting full file (no line range specified), use cached result
    if line_start is None and line_end is None:
        content = full_content
    else:
        # Otherwise, make a second request with the specific range
        params = {"path": path, "line_start": actual_start, "line_end": actual_end}
        result = await _rag_get_request("/files/content", params)

        if not result.get("success"):
            return result

        content = result.get("content", "")

    # Build line index strings (1-indexed format)
    total_line_index = f"1-{total_lines}"
    selected_line_index = f"{actual_start}-{actual_end}"

    # Build note if any adjustment was made
    note = None
    if original_line_end is not None and line_end != original_line_end:
        note = f" (Requested line_end {original_line_end} exceeded file length. Auto-adjusted to {line_end})."
    elif line_end is None and line_start is not None:
        note = f" (Reading from line {line_start} to end of file: line {total_lines})."

    return {
        "success": True,
        "path": path,
        "total_line_index": total_line_index,
        "selected_line_index": selected_line_index + (note if note else ""),
        "content": content,
    }


@mcp.tool()
async def get_markdown_structure(path: str):
    """Analyze markdown file structure (headings hierarchy and statistics).

    This tool parses a markdown file and extracts its structural
    information, including all headings with their levels and
    line numbers, along with file statistics.

    When to use:
        - Understanding document structure before reading
        - Navigating to specific sections
        - Getting an overview of markdown content
        - Building table of contents for documentation

    Args:
        path (str): Relative path to markdown file within load directory.
                   Examples:
                     - "README.md"
                     - "docs/api_reference.md"
                     - "notes/lecture_01.md"
    Notes:
        - Only works with .md files
        - Headings in code blocks are excluded
        - Headings are ordered by appearance in file
        - Use get_file_content to read specific sections
    """
    result = await _rag_get_request("/files/markdown/structure", {"path": path})

    if not result.get("success"):
        return result

    headings = result.get("headings", [])
    if not headings:
        return {
            "success": True,
            "path": path,
            "structure": "No headings found in this markdown file.",
            "total_lines": result.get("total_lines", 0),
            "heading_count": 0,
            "code_block_count": result.get("code_block_count", 0),
            "statistics": f"Total lines: {result.get('total_lines', 0)}, Code blocks: {result.get('code_block_count', 0)}",
        }

    # Format headings into human-readable structure
    structure_lines = []

    for heading in headings:
        level = heading.get("level", 1)
        text = heading.get("text", "")
        line_number = heading.get("line_number", 0)

        # Calculate indentation based on heading level (H1=0, H2=2, H3=4, ...)
        indent = "  " * (level - 1)

        # Format heading with line number
        heading_marker = "#" * level
        formatted_line = f'{indent}{heading_marker} {text} (line {line_number})'
        structure_lines.append(formatted_line)

    structure_string = "\n".join(structure_lines)

    # Build statistics summary
    total_lines = result.get("total_lines", 0)
    heading_count = len(headings)
    code_block_count = result.get("code_block_count", 0)

    stats_summary = (
        f"Total lines: {total_lines}\n"
        f"Headings: {heading_count}\n"
        f"Code blocks: {code_block_count}"
    )

    return {
        "success": True,
        "path": path,
        "structure": structure_string,
        "total_lines": total_lines,
        "heading_count": heading_count,
        "code_block_count": code_block_count,
        "statistics": stats_summary,
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
