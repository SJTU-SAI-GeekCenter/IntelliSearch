from typing import Any

try:
    from security import validate_path, SecurityError
except ImportError:
    from .security import validate_path, SecurityError
import logging

logger = logging.getLogger("filesystem-write")


def write_file_impl(path: str, content: str) -> str:
    """
    写入文件 (覆盖或创建) Implementation
    Autodetects whether to require 'write' or 'create' permission.
    """
    try:
        # Check existence to decide permission (simplistic approach)
        # We catch exceptions in case 'read' is denied but 'write' might be allowed blind (rare but possible)
        exists = False
        try:
            p = validate_path(path, action="read")
            exists = p.exists()
        except Exception:
            pass  # proceed to verify write/create specifically

        required_action = "write" if exists else "create"
        target_path = validate_path(path, action=required_action)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully {'Overwritten' if exists else 'Created'} file '{path}' ({len(content)} chars)."

    except SecurityError:
        raise
    except Exception as e:
        return f"Error writing file: {str(e)}"


def append_file_impl(path: str, content: str) -> str:
    """
    Append content to a file.
    """
    try:
        # Check if file exists to determine message
        exists = False
        try:
            p = validate_path(path, action="read")
            exists = p.exists()
        except Exception:
            pass

        # Validate path for write permission
        target_path = validate_path(path, action="write")

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(content)

        action = "Appended to" if exists else "Created and appended to"
        return f"Successfully {action} file '{path}' (added {len(content)} chars)."

    except SecurityError:
        raise
    except Exception as e:
        return f"Error appending to file: {str(e)}"
