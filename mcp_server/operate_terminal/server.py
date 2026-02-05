import subprocess
import os
import platform
from mcp.server.fastmcp import FastMCP
from typing import Optional

mcp = FastMCP("Operate-Terminals")

# TODO We need to implement more!


@mcp.tool()
def execute_command(command: str, timeout: int = 30) -> str:
    """
    Executes a shell command and returns its stdout and stderr.

    Args:
        command (str): The shell command to execute.
        timeout (int): Maximum execution time in seconds. Defaults to 30.

    Returns:
        str: Combined output of stdout and stderr, or an error message.
    """
    try:
        process = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )

        output = []
        if process.stdout:
            output.append(f"STDOUT:\n{process.stdout}")
        if process.stderr:
            output.append(f"STDERR:\n{process.stderr}")

        return "\n".join(output) if output else "Command executed with no output."

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def get_basic_info() -> dict:
    """
    Retrieves system environment information including OS, Python version, and key paths.

    Returns:
        dict: A dictionary containing OS details, current user, and environment variables.
    """
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "current_user": os.getlogin() if hasattr(os, "getlogin") else "unknown",
        "current_working_dir": os.getcwd(),
        "python_version": platform.python_version(),
        "path_separator": os.pathsep,
    }


@mcp.tool()
def get_environments() -> dict:
    """Get current environment variables in the current sessions.

    Returns:
        dict: A dictionary which is equal to `os.environ`
    """
    return os.environ


@mcp.tool()
def check_command_exists(command_name: str) -> str:
    """
    Checks if a specific command or executable is available in the system PATH.
    Useful for checking dependencies like 'git', 'docker', or 'npm'.

    Args:
        command_name (str): The name of the command to check.
    """
    from shutil import which

    path = which(command_name)
    if path:
        return f"Command '{command_name}' is available at: {path}"
    return f"Command '{command_name}' was not found in the system PATH."


@mcp.tool()
def list_running_processes(filter_name: Optional[str] = None) -> str:
    """
    Lists currently running processes. Can be filtered by process name.

    Args:
        filter_name (str, optional): Only return processes containing this string.
    """
    try:
        if platform.system() == "Windows":
            cmd = "tasklist"
        else:
            cmd = "ps aux"

        result = subprocess.check_output(cmd, shell=True, text=True)

        if filter_name:
            lines = [
                line
                for line in result.split("\n")
                if filter_name.lower() in line.lower()
            ]
            return (
                "\n".join(lines)
                if lines
                else f"No processes found matching: {filter_name}"
            )

        return result[:2000] + "\n...(truncated)"
    except Exception as e:
        return f"Failed to list processes: {str(e)}"


if __name__ == "__main__":
    mcp.run()
