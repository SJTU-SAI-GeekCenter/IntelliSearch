import time
import sys
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    from security_prompt import ensure_path_access
except ImportError:
    from .security_prompt import ensure_path_access


def list_directory_impl(path: str = ".") -> str:
    """
    列出目录内容 Implementation
    """
    try:
        target_path = ensure_path_access(path, action="read")

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."
        if not target_path.is_dir():
            return f"Error: Path '{path}' is not a directory."

        items = []
        # 排序以保证输出确定性
        for item in sorted(target_path.iterdir()):
            try:
                type_str = "<DIR>" if item.is_dir() else "<FILE>"

                # 获取文件大小和时间
                size_str = ""
                if item.is_file():
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"

                    # 修改时间
                mtime = item.stat().st_mtime
                time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))

                # items.append(f"{type_str:<5} {item.name:<30} {size_str}")
                # 优化格式: 类型 | 大小 | 时间 | 名称
                items.append(f"{type_str:<6} {size_str:<10} {time_str:<16} {item.name}")
            except PermissionError:
                # 跳过无权限访问的文件/目录
                continue

        result = f"Directory listing for '{path}':\n"
        result += f"{'Type':<6} {'Size':<10} {'Modified':<16} {'Name'}\n"
        result += "-" * 60 + "\n"
        result += "\n".join(items)
        if not items:
            result += "(empty directory)"

        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def list_tree_impl(path: str = ".", max_depth: int = -1) -> str:
    """
    Recursively list directory contents (tree view).
    max_depth: -1 for unlimited (careful), or integer for specific depth (e.g. 2).
    """
    try:
        target_path = ensure_path_access(path, action="read")

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."
        if not target_path.is_dir():
            return f"Error: Path '{path}' is not a directory."

        tree_lines = []

        def _walk(p, prefix="", current_depth=0):
            if max_depth != -1 and current_depth >= max_depth:
                return

            try:
                # iterdir can fail if no permission
                contents = sorted(list(p.iterdir()))
            except PermissionError:
                # 显示 (Access Denied) 并继续
                tree_lines.append(f"{prefix}└── (Access Denied)")
                return

            count = len(contents)
            for index, item in enumerate(contents):
                try:
                    is_last = index == count - 1
                    connector = "└── " if is_last else "├── "

                    type_mark = "/" if item.is_dir() else ""
                    tree_lines.append(f"{prefix}{connector}{item.name}{type_mark}")

                    if item.is_dir():
                        extension = "    " if is_last else "│   "
                        _walk(item, prefix + extension, current_depth + 1)
                except PermissionError:
                    # 跳过无权限访问的文件/目录
                    continue

        tree_lines.append(f"{target_path.name}/")
        _walk(target_path)

        return "\n".join(tree_lines)

    except Exception as e:
        return f"Error walking directory tree: {str(e)}"
