from typing import Any
from pathlib import Path
import logging

logger = logging.getLogger("filesystem-write")


def write_file_impl(path: str, content: str) -> str:
    """
    写入文件 (覆盖或创建) Implementation
    """
    try:
        target_path = Path(path).resolve()

        # Check if file exists
        exists = target_path.exists()

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully {'Overwritten' if exists else 'Created'} file '{path}' ({len(content)} chars)."

    except Exception as e:
        return f"Error writing file: {str(e)}"


def append_file_impl(path: str, content: str) -> str:
    """
    Append content to a file.
    """
    try:
        target_path = Path(path).resolve()

        # Check if file exists
        exists = target_path.exists()

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(content)

        action = "Appended to" if exists else "Created and appended to"
        return f"Successfully {action} file '{path}' (added {len(content)} chars)."

    except Exception as e:
        return f"Error appending to file: {str(e)}"
