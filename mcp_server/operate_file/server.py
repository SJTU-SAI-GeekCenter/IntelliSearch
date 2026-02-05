import os
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Operate-Files")

# todo 总体目标
# 实现本地文件操作的工具设计
# * 设计的工具内容都是涉及文件的 CRUD 封装操作
# * WE NEED MORE! 实现对不同类别文件的单独操作
# e.g. pandas operations for csv files
# e.g. simple operations for pdf files & png files
# e.g. AST Parser & JSON Parser for files

# 具体任务：
# 完成若干 @mcp.tool() 的函数实现
# 优化 Docstring


@mcp.tool()
def create_folder(path: str) -> str:
    """Create a new folder at the specified path.

    Args:
        path (str): The path where the folder should be created.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_directory(path: str) -> list:
    """List all files and subdirectories in the specified directory.

    Args:
        path (str): The path of the directory to list.

    Returns:
        list: A list of file and directory names, or an error message.
    """
    try:
        list_dir = os.listdir(path)
        return f"LIST_FILE_PATH: {list_dir}"
    except Exception as e:
        return [f"Error: {e}"]


@mcp.tool()
def delete_item(path: str) -> str:
    """Delete the specified file or folder.

    Args:
        path (str): The path of the item to delete.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def rename_item(src: str, dest: str) -> str:
    """Rename a file or folder.

    Args:
        src (str): The current path of the item.
        dest (str): The new path for the item.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        os.rename(src, dest)
        return f"Renamed {src} to {dest}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def move_file(src: str, dest: str) -> str:
    """Move a file to a new location.

    Args:
        src (str): The current path of the file.
        dest (str): The destination path for the file.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        shutil.move(src, dest)
        return f"Moved {src} to {dest}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path (str): The path of the file to read.

    Returns:
        str: The file contents or an error message.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file.

    Args:
        path (str): The path of the file to write to.
        content (str): The content to write to the file.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_file_info(path: str) -> dict:
    """Get information about a file or directory.

    Args:
        path (str): The path of the file or directory.

    Returns:
        dict: A dictionary containing file information or an error message.
    """
    try:
        stat = os.stat(path)
        return {
            "path": path,
            "size": stat.st_size,
            "is_directory": os.path.isdir(path),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_current_directory() -> str:
    """Get the current working directory.

    Returns:
        str: The current working directory path.
    """
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def create_file(path: str) -> str:
    """Create a new empty file at the specified path.

    Args:
        path (str): The path where the file should be created.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        with open(path, "w") as file:
            pass  # Create an empty file
        return f"Created file: {path}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()