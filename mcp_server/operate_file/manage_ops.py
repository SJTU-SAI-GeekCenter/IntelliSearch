import os
import shutil
from pathlib import Path

try:
    from security import validate_path, SecurityError
except ImportError:
    from .security import validate_path, SecurityError


def mkdir_impl(path: str) -> str:
    """Create a new directory (recursive)."""
    try:
        target_path = validate_path(path, action="create")
        os.makedirs(target_path, exist_ok=True)
        return f"Successfully created directory: {target_path}"
    except SecurityError:
        raise
    except Exception as e:
        return f"Error creating directory: {str(e)}"


def rm_impl(path: str) -> str:
    """Run delete command on path (file or folder)."""
    try:
        target_path = validate_path(path, action="delete")

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."

        if target_path.is_dir():
            shutil.rmtree(target_path)
            return f"Successfully removed directory tree: {target_path}"
        else:
            target_path.unlink()
            return f"Successfully removed file: {target_path}"

    except SecurityError:
        raise
    except Exception as e:
        return f"Error removing '{path}': {str(e)}"


def mv_impl(src: str, dest: str) -> str:
    """Move file or directory."""
    try:
        # Check Source Permission (Need Delete because it disappears)
        src_path = validate_path(src, action="delete")
        if not src_path.exists():
            return f"Error: Source '{src}' does not exist."

        # Check Dest Permission (Need Create because it appears)
        # Note: shutil.move might overwrite? If so, we might need 'write' too.
        # But for simplicity, we use 'create' as the primary gate for new location.
        dest_path = validate_path(dest, action="create")

        shutil.move(str(src_path), str(dest_path))
        return f"Successfully moved '{src}' to '{dest}'"
    except SecurityError:
        raise
    except Exception as e:
        return f"Error moving: {str(e)}"


def copy_impl(src: str, dest: str) -> str:
    """Copy file or directory."""
    try:
        # Check Source Permission (Read)
        src_path = validate_path(src, action="read")
        if not src_path.exists():
            return f"Error: Source '{src}' does not exist."

        # Check Dest Permission (Create)
        dest_path = validate_path(dest, action="create")

        if src_path.is_dir():
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            return f"Successfully copied directory '{src}' to '{dest}'"
        else:
            shutil.copy2(src_path, dest_path)
            return f"Successfully copied file '{src}' to '{dest}'"

    except SecurityError:
        raise
    except Exception as e:
        return f"Error copying '{src}' to '{dest}': {str(e)}"
