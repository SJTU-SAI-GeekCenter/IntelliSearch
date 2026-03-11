import os
import shutil
from pathlib import Path


def mkdir_impl(path: str) -> str:
    """Create a new directory (recursive)."""
    try:
        target_path = Path(path).resolve()
        os.makedirs(target_path, exist_ok=True)
        return f"Successfully created directory: {target_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


def rm_impl(path: str) -> str:
    """Run delete command on path (file or folder)."""
    try:
        target_path = Path(path).resolve()

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."

        if target_path.is_dir():
            shutil.rmtree(target_path)
            return f"Successfully removed directory tree: {target_path}"
        else:
            target_path.unlink()
            return f"Successfully removed file: {target_path}"

    except Exception as e:
        return f"Error removing '{path}': {str(e)}"


def mv_impl(src: str, dest: str) -> str:
    """Move file or directory."""
    try:
        src_path = Path(src).resolve()
        if not src_path.exists():
            return f"Error: Source '{src}' does not exist."

        dest_path = Path(dest).resolve()

        shutil.move(str(src_path), str(dest_path))
        return f"Successfully moved '{src}' to '{dest}'"
    except Exception as e:
        return f"Error moving: {str(e)}"


def copy_impl(src: str, dest: str) -> str:
    """Copy file or directory."""
    try:
        src_path = Path(src).resolve()
        if not src_path.exists():
            return f"Error: Source '{src}' does not exist."

        dest_path = Path(dest).resolve()

        if src_path.is_dir():
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            return f"Successfully copied directory '{src}' to '{dest}'"
        else:
            shutil.copy2(src_path, dest_path)
            return f"Successfully copied file '{src}' to '{dest}'"

    except Exception as e:
        return f"Error copying '{src}' to '{dest}': {str(e)}"
