import sys
import os
import logging
from mcp.server.fastmcp import FastMCP

# Ensure the current directory is in the path so imports work when run as a script
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try direct imports first (for script execution)
    from list_ops import list_directory_impl, list_tree_impl
    from read_ops import read_file_impl, search_files_impl
    from write_ops import write_file_impl, append_file_impl
    from manage_ops import mkdir_impl, rm_impl, mv_impl, copy_impl
except ImportError:
    # Fallback to relative imports (for module execution)
    from .list_ops import list_directory_impl, list_tree_impl
    from .read_ops import read_file_impl, search_files_impl
    from .write_ops import write_file_impl, append_file_impl
    from .manage_ops import mkdir_impl, rm_impl, mv_impl, copy_impl

# Initialize FastMCP Server
mcp = FastMCP("operate_file")


@mcp.tool()
def ls(path: str = ".") -> str:
    """
    List directory contents with details (size, time).
    Recommended for checking specific folders. For overview, use 'tree' instead.

    Args:
        path: Directory path (relative to allowed root or absolute). Defaults to current directory.
    """
    return list_directory_impl(path)


@mcp.tool()
def cat(path: str) -> str:
    """
    Read file content. Supports text files and PDF (extracts text). Excel preview is disabled.

    [Optimization]
    If the file is large (>100 lines) or you only need specific information, prefer using 'search_files' first.

    Args:
        path: File path to read.
    """
    return read_file_impl(path)


@mcp.tool()
def touch(path: str, content: str = "") -> str:
    """
    Create or update a file with content.

    [CAUTION]
    This will OVERWRITE existing files completely. To add content, use 'append' instead.

    Args:
        path: File path to write to.
        content: Text content to write.
    """
    return write_file_impl(path, content)


@mcp.tool()
def mkdir(path: str) -> str:
    """
    Create a new directory (recursive).
    Args:
        path: Directory path to create.
    """
    return mkdir_impl(path)


@mcp.tool()
def rm(path: str) -> str:
    """
    Remove a file or directory.

    [WARNING]
    This action is IRREVERSIBLE. Check contents with 'ls' or 'tree' before deleting directories.
    Do not delete files unless explicitly requested by the user.

    Args:
        path: Path to remove.
    """
    return rm_impl(path)


@mcp.tool()
def mv(src: str, dest: str) -> str:
    """
    Move or rename a file or directory.
    Args:
        src: Source path.
        dest: Destination path.
    """
    return mv_impl(src, dest)


@mcp.tool()
def copy(src: str, dest: str) -> str:
    """
    Copy a file or directory (recursive).
    Args:
        src: Source path.
        dest: Destination path.
    """
    return copy_impl(src, dest)


@mcp.tool()
def append(path: str, content: str) -> str:
    """
    Append content to a file.
    Args:
        path: File path to append to.
        content: Text content to append.
    """
    return append_file_impl(path, content)


@mcp.tool()
def tree(path: str = ".", max_depth: int = 2) -> str:
    """
    Recursively list directory contents in a tree structure.

    [IMPORTANT]
    - ALWAYS specify a constrained 'max_depth' (e.g. 2 or 3) to prevent context overflow.
    - Default is depth 2. Use -1 only if you are sure the directory is small.

    Args:
        path: Root directory path.
        max_depth: Maximum depth to traverse. Defaults to 2.
    """
    return list_tree_impl(path, max_depth)


@mcp.tool()
def search_files(path: str, pattern: str) -> str:
    """
    Search for a text pattern in files within a directory used for grep.

    [Hint]
    Use specific, unique keywords. Common words will return too many results.

    Args:
        path: Root directory to search in.
        pattern: Text pattern to search for.
    """
    return search_files_impl(path, pattern)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run()
