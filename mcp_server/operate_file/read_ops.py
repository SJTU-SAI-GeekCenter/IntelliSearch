from typing import Any
from pathlib import Path

try:
    from security import validate_path, SecurityError
except ImportError:
    from .security import validate_path, SecurityError


def read_pdf(file_path) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(file_path)
        text = []
        num_pages = len(reader.pages)
        max_pages = 20  # Limit pages to prevent context overflow

        header = f"--- PDF Content ({num_pages} pages, extracting first {min(num_pages, max_pages)}) ---\n"

        for i, page in enumerate(reader.pages):
            if i >= max_pages:
                text.append(
                    f"\n... (Remaining {num_pages - max_pages} pages omitted) ..."
                )
                break
            text.append(f"[Page {i+1}]\n{page.extract_text()}")

        return header + "\n".join(text)
    except ImportError:
        return "[Error: 'pypdf' library not installed. Cannot read PDF.]"
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"


def read_file_impl(path: str) -> str:
    """
    智能读取文件 Implementation
    """
    try:
        target_path = validate_path(path)

        if not target_path.exists():
            return f"Error: File '{path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{path}' is a directory."

        # 根据扩展名分发
        suffix = target_path.suffix.lower()

        if suffix == ".pdf":
            return read_pdf(target_path)
        elif suffix in [".xlsx", ".xls"]:
            return "[Excel preview disabled. Please use a custom Python script to read this file.]"
        elif suffix in [".jpg", ".png", ".jpeg", ".gif"]:
            return f"[Image file: {target_path.name}] (Content viewing not supported yet, utilize specific vision tools if available)"

        # 默认尝试文本读取
        try:
            # 限制读取大小，例如 100KB
            file_size = target_path.stat().st_size
            if file_size > 100 * 1024:
                return f"Error: File is too large ({file_size} bytes). Please use 'search_files' or read specific chunks (not implemented yet)."

            # 尝试多种编码读取
            content = None
            encodings = ["utf-8", "gbk", "latin-1"]

            for enc in encodings:
                try:
                    with open(target_path, "r", encoding=enc) as f:
                        content = f.read()
                    break  # Success
                except UnicodeDecodeError:
                    continue

            if content is None:
                return f"[Binary file detected: {target_path.name}. Content cannot be displayed as text.]"

            return content

        except Exception as e:
            return f"Error reading file content: {str(e)}"

    except SecurityError:
        raise
    except Exception as e:
        return f"Error reading file: {str(e)}"


def search_files_impl(path: str, pattern: str) -> str:
    """
    Search for a text pattern in files within a directory (recursive).
    """
    try:
        target_path = validate_path(path)

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."
        if not target_path.is_dir():
            return f"Error: '{path}' must be a directory for search."

        results = []
        max_results = 50
        matches_found = 0

        import os

        # Simple walk
        for root, dirs, files in os.walk(target_path):
            if matches_found >= max_results:
                break

            for file in files:
                file_path = Path(root) / file

                # Basic extension check to skip obvious binaries
                if file_path.suffix.lower() in [
                    ".pyc",
                    ".exe",
                    ".dll",
                    ".so",
                    ".bin",
                    ".zip",
                    ".jpg",
                    ".png",
                    ".git",
                ]:
                    continue

                try:
                    # Check for binary content by reading first 1024 bytes
                    is_binary = False
                    with open(file_path, "rb") as f:
                        chunk = f.read(1024)
                        if b"\0" in chunk:
                            is_binary = True

                    if is_binary:
                        continue

                    # Try reading as text with fallback encoding (gbk for windows)
                    content = None
                    for enc in ["utf-8", "gbk", "latin-1"]:
                        try:
                            with open(file_path, "r", encoding=enc) as f:
                                content = f.readlines()
                            break
                        except UnicodeDecodeError:
                            continue

                    if content is None:
                        continue

                    for i, line in enumerate(content):
                        if pattern in line:
                            rel_path = file_path.relative_to(target_path)
                            # Truncate line if too long
                            clean_line = line.strip()[:200]
                            results.append(f"{rel_path}:{i+1}: {clean_line}")
                            matches_found += 1
                            if matches_found >= max_results:
                                break
                except Exception:
                    continue  # Skip unreadable

        if not results:
            return f"No matches found for '{pattern}' in '{path}'."

        header = f"Search results for '{pattern}' in '{path}':\n" + "-" * 50 + "\n"
        footer = (
            f"\n(Showing first {len(results)} matches)"
            if len(results) == max_results
            else ""
        )
        return header + "\n".join(results) + footer

    except SecurityError:
        raise
    except Exception as e:
        return f"Error searching files: {str(e)}"
