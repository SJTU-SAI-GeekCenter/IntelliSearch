import subprocess
import os
import json
import platform
import shutil
import psutil
import socket
import time
from shutil import which
from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict

mcp = FastMCP("Operate-Terminals")

# ===================================
# Basic Tools
# ===================================

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
    return json.dumps(dict(os.environ), ensure_ascii=False, indent=2)


@mcp.tool()
def check_command_exists(command_name: str) -> str:
    """
    Checks if a specific command or executable is available in the system PATH.
    Useful for checking dependencies like 'git', 'docker', or 'npm'.

    Args:
        command_name (str): The name of the command to check.
    """
    

    path = which(command_name)
    if path:
        return f"Command '{command_name}' is available at: {path}"
    return f"Command '{command_name}' was not found in the system PATH."


# ===================================
# Checking and Managing Processes
# ===================================


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
    
@mcp.tool()
def get_process_details(pid: int) -> str:
    """
    Retrieves detailed information about a specific process including resource usage.

    This function provides comprehensive details about a running process including
    CPU and memory utilization, status, creation time, and open connections.

    Args:
        pid (int): The Process ID (PID) of the target process. Use list_running_processes
                   to find available PIDs.

    Returns:
        str: A formatted string containing detailed process information including:
             - Process name and PID
             - Current status (running, sleeping, zombie, etc.)
             - CPU utilization percentage
             - Memory usage (RSS, VMS) and percentage
             - Number of threads
             - Process creation time
             - Command line arguments
             - Or an error message if the process is not found or access is denied.

    Example:
        >>> get_process_details(1234)
        "Process Details:\\nName: python3\\nPID: 1234\\nStatus: running\\n..."
    """
    try:
        process = psutil.Process(pid)

        # Basic information
        name = process.name()
        status = process.status()
        create_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(process.create_time())
        )

        # CPU and Memory
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # Threads and connections
        num_threads = process.num_threads()
        try:
            connections = process.net_connections(kind="inet")
            num_connections = len(connections)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            num_connections = 0

        # Command line
        try:
            cmdline = " ".join(process.cmdline())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            cmdline = "Access denied or process not found"

        # Format output
        details = [
            f"Process Details:",
            f"  Name: {name}",
            f"  PID: {pid}",
            f"  Status: {status}",
            f"  CPU Usage: {cpu_percent}%",
            f"  Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB",
            f"  Memory Percentage: {memory_percent:.2f}%",
            f"  Threads: {num_threads}",
            f"  Network Connections: {num_connections}",
            f"  Created: {create_time}",
            f"  Command: {cmdline}",
        ]

        return "\n".join(details)

    except psutil.NoSuchProcess:
        return f"Error: Process with PID {pid} not found."
    except psutil.AccessDenied:
        return f"Error: Access denied to process {pid}. Try running with elevated privileges."
    except Exception as e:
        return f"Error: Failed to get process details: {str(e)}"



# ===================================
# Network Utilities
# ===================================

@mcp.tool()
def check_port(port: int, host: str = "localhost") -> str:
    """
    Checks if a specific network port is currently in use or available.

    This function attempts to connect to the specified port and host to determine
    if the port is open and being used by a service. Useful for checking if a
    service is running or finding an available port for new services.

    Args:
        port (int): The port number to check (0-65535). Common ports include:
                    - 22: SSH
                    - 80: HTTP
                    - 443: HTTPS
                    - 3000: Development servers
                    - 5000-9000: Various application servers
        host (str): The hostname or IP address to check. Defaults to "localhost".
                    Can be an IP address (e.g., "127.0.0.1") or hostname.

    Returns:
        str: A message indicating whether the port is open (in use) or closed (available).
             Also includes the process name using the port if available.

    Example:
        >>> check_port(3000)
        "Port 3000 is OPEN on localhost. Used by: node"
        >>> check_port(9999)
        "Port 9999 is CLOSED on localhost. Available for use."
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))

            if result == 0:
                # Port is open, try to find the process using it
                process_name = "Unknown"
                try:
                    for conn in psutil.net_connections():
                        if conn.laddr.port == port and conn.status == "LISTEN":
                            try:
                                process = psutil.Process(conn.pid)
                                process_name = process.name()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                            break
                except (psutil.AccessDenied, Exception):
                    pass

                return (
                    f"Port {port} is OPEN on {host}. Currently in use by: {process_name}"
                )
            else:
                return f"Port {port} is CLOSED on {host}. Available for use."

    except socket.gaierror:
        return f"Error: Could not resolve hostname '{host}'."
    except Exception as e:
        return f"Error: Failed to check port {port}: {str(e)}"


@mcp.tool()
def test_connection(host: str, port: Optional[int] = None, timeout: int = 5) -> str:
    """
    Tests network connectivity to a specified host and optional port.

    This function verifies network connectivity by attempting to establish a
    connection to the target host. Can test basic connectivity (ping-like) or
    specific port connectivity (e.g., HTTP server on port 80).

    Args:
        host (str): The hostname or IP address to test. Examples:
                    - "google.com"
                    - "192.168.1.1"
                    - "localhost"
        port (int, optional): Specific port number to test. If None, only tests
                             basic DNS resolution. Examples:
                             - 80 for HTTP
                             - 443 for HTTPS
                             - 22 for SSH
        timeout (int): Connection timeout in seconds. Defaults to 5. Longer timeouts
                      may be needed for slow or distant networks.

    Returns:
        str: A detailed report of the connection test including:
             - DNS resolution status
             - Connection success/failure
             - Response time (if successful)
             - Diagnostic information (if failed)

    Example:
        >>> test_connection("google.com", 443)
        "Testing connection to google.com:443...\\nDNS Resolution: SUCCESS\\n..."
    """
    results = []
    results.append(f"Testing connection to {host}" + (f":{port}" if port else "") + "...")

    # Test DNS resolution
    try:
        ip_address = socket.gethostbyname(host)
        results.append(f"DNS Resolution: SUCCESS ({ip_address})")
    except socket.gaierror:
        results.append("DNS Resolution: FAILED - Could not resolve hostname")
        return "\n".join(results)

    # Test port connection if specified
    if port:
        try:
            start_time = time.time()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((host, port))
                elapsed = time.time() - start_time

                if result == 0:
                    results.append(f"Connection: SUCCESS (responded in {elapsed:.3f}s)")
                    results.append(f"Port {port} on {host} is reachable.")
                else:
                    results.append(
                        f"Connection: FAILED - Port {port} is not accessible"
                    )
        except socket.timeout:
            results.append(f"Connection: TIMEOUT after {timeout}s")
        except Exception as e:
            results.append(f"Connection: ERROR - {str(e)}")
    else:
        results.append("Connection: SKIPPED (no port specified)")

    return "\n".join(results)


@mcp.tool()
def get_network_info() -> str:
    """
    Retrieves comprehensive network configuration and statistics for the system.

    This function provides detailed information about network interfaces,
    IP addresses, MAC addresses, network I/O statistics, and active connections.
    Useful for diagnosing network issues or understanding network configuration.

    Returns:
        str: A formatted report containing:
             - Network interfaces and their statuses (up/down)
             - IP addresses (IPv4 and IPv6) for each interface
             - MAC addresses for each interface
             - Network I/O statistics (bytes sent/received, packets sent/received)
             - Active TCP/UDP connections summary
             - Or an error message if information cannot be retrieved.

    Example:
        >>> get_network_info()
        "Network Configuration:\\n\\nInterfaces:\\n  lo (127.0.0.1) - UP\\n  ..."
    """
    try:
        info = ["Network Configuration:\n"]

        # Network interfaces
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        info.append("Interfaces:")
        for interface_name, addresses in interfaces.items():
            interface_info = f"  {interface_name}: "

            # Get status
            if interface_name in stats:
                is_up = stats[interface_name].isup
                interface_info += f"{'UP' if is_up else 'DOWN'}"

            # Get addresses
            ip_addresses = []
            mac_address = None
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    ip_addresses.append(addr.address)
                elif addr.family == socket.AF_INET6:
                    ip_addresses.append(f"{addr.address}%{interface_name}")
                elif addr.family == psutil.AF_LINK:
                    mac_address = addr.address

            if ip_addresses:
                interface_info += f" | IPs: {', '.join(ip_addresses)}"
            if mac_address:
                interface_info += f" | MAC: {mac_address}"

            info.append(interface_info)

        # Network I/O statistics
        info.append("\nNetwork I/O Statistics:")
        net_io = psutil.net_io_counters()
        info.append(f"  Bytes Sent: {net_io.bytes_sent:,}")
        info.append(f"  Bytes Received: {net_io.bytes_recv:,}")
        info.append(f"  Packets Sent: {net_io.packets_sent:,}")
        info.append(f"  Packets Received: {net_io.packets_recv:,}")
        info.append(f"  Errors In: {net_io.errin:,}")
        info.append(f"  Errors Out: {net_io.errout:,}")
        info.append(f"  Drops In: {net_io.dropin:,}")
        info.append(f"  Drops Out: {net_io.dropout:,}")

        # Connection summary
        info.append("\nActive Connections:")
        connections = psutil.net_connections(kind="inet")
        established = sum(1 for c in connections if c.status == "ESTABLISHED")
        listen = sum(1 for c in connections if c.status == "LISTEN")
        info.append(f"  Established: {established}")
        info.append(f"  Listening: {listen}")
        info.append(f"  Total: {len(connections)}")

        return "\n".join(info)

    except psutil.AccessDenied:
        return "Error: Access denied. Try running with elevated privileges."
    except Exception as e:
        return f"Error: Failed to get network info: {str(e)}"


# ===================================
# System Monitoring
# ===================================


@mcp.tool()
def get_disk_usage(path: str = "/") -> str:
    """
    Retrieves disk usage statistics for a specified filesystem path.

    This function provides comprehensive disk storage information including total
    capacity, used space, free space, and usage percentages. Useful for monitoring
    disk space and preventing storage issues.

    Args:
        path (str): The filesystem path to check. Defaults to "/" (root on Unix/Mac).
                    On Windows, use "C:\\", "D:\\", etc. The path can be any
                    directory path - usage is reported for the filesystem containing
                    that path.

    Returns:
        str: A formatted report containing:
             - Filesystem mount point
             - Total disk capacity in GB
             - Used disk space in GB
             - Free disk space in GB
             - Usage percentage with visual indicator
             - Or an error message if the path is invalid or inaccessible.

    Example:
        >>> get_disk_usage("/")
        "Disk Usage for /:\\n  Total: 500.0 GB\\n  Used: 250.5 GB (50%)\\n  ..."
        >>> get_disk_usage("C:\\\\")
        "Disk Usage for C:\\:\\n  Total: 1.0 TB\\n  Used: 600.2 GB (60%)\\n  ..."
    """
    try:
        usage = psutil.disk_usage(path)

        # Convert to GB
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        percent = usage.percent

        # Create visual bar
        bar_length = 20
        filled = int(bar_length * percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        info = [
            f"Disk Usage for {path}:",
            f"  Total: {total_gb:.2f} GB",
            f"  Used: {used_gb:.2f} GB ({percent}%)",
            f"  Free: {free_gb:.2f} GB",
            f"  Usage: [{bar}]",
        ]

        return "\n".join(info)

    except FileNotFoundError:
        return f"Error: Path '{path}' does not exist."
    except PermissionError:
        return f"Error: Permission denied to access '{path}'."
    except Exception as e:
        return f"Error: Failed to get disk usage for '{path}': {str(e)}"


@mcp.tool()
def get_memory_usage() -> str:
    """
    Retrieves detailed memory usage statistics for the system.

    This function provides comprehensive memory information including physical RAM,
    swap space, and per-process memory breakdown. Useful for identifying memory
    leaks or performance bottlenecks.

    Returns:
        str: A formatted report containing:
             - Total physical memory
             - Available memory
             - Used memory with percentage
             - Memory usage breakdown by top 5 processes
             - Swap memory statistics (if available)
             - Visual usage indicators
             - Or an error message if information cannot be retrieved.

    Example:
        >>> get_memory_usage()
        "Memory Usage:\\n  Physical Memory:\\n    Total: 16.0 GB\\n    ..."
    """
    try:
        info = ["Memory Usage:\n"]

        # Physical memory (RAM)
        mem = psutil.virtual_memory()
        info.append("Physical Memory (RAM):")
        info.append(f"  Total: {mem.total / (1024**3):.2f} GB")
        info.append(f"  Available: {mem.available / (1024**3):.2f} GB")
        info.append(f"  Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
        info.append(f"  Free: {mem.free / (1024**3):.2f} GB")

        # Visual bar for memory
        bar_length = 20
        filled = int(bar_length * mem.percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        info.append(f"  Usage: [{bar}]")

        # Swap memory
        swap = psutil.swap_memory()
        info.append("\nSwap Memory:")
        info.append(f"  Total: {swap.total / (1024**3):.2f} GB")
        info.append(f"  Used: {swap.used / (1024**3):.2f} GB ({swap.percent}%)")
        info.append(f"  Free: {swap.free / (1024**3):.2f} GB")

        # Top 5 memory-consuming processes
        info.append("\nTop 5 Memory-Consuming Processes:")
        processes = []
        for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by memory usage and get top 5
        processes.sort(key=lambda p: p["memory_percent"], reverse=True)
        for i, proc in enumerate(processes[:5], 1):
            info.append(
                f"  {i}. PID {proc['pid']:>6} | {proc['name']:<20} | {proc['memory_percent']:.2f}%"
            )

        return "\n".join(info)

    except Exception as e:
        return f"Error: Failed to get memory usage: {str(e)}"


@mcp.tool()
def get_cpu_usage(per_cpu: bool = False, interval: float = 0.5) -> str:
    """
    Retrieves CPU usage statistics and load information.

    This function provides detailed CPU utilization data including overall usage,
    per-core breakdown, load averages, and CPU frequency. Useful for monitoring
    system performance and identifying CPU bottlenecks.

    Args:
        per_cpu (bool): If True, returns usage for each CPU core individually.
                       If False, returns average usage across all cores.
                       Defaults to False.
        interval (float): Time interval in seconds to measure CPU usage.
                         Longer intervals provide more accurate measurements.
                         Defaults to 0.5 seconds. Range: 0.1-5.0 recommended.

    Returns:
        str: A formatted report containing:
             - CPU usage percentage (average or per-core)
             - Number of physical and logical cores
             - CPU frequency (current, min, max) if available
             - Load averages (1, 5, 15 minutes) on Unix/Mac
             - CPU usage by top 5 processes
             - Visual usage indicators
             - Or an error message if information cannot be retrieved.

    Example:
        >>> get_cpu_usage()
        "CPU Usage:\\n  Overall: 25.5%\\n  Cores: 8 physical, 16 logical\\n  ..."
        >>> get_cpu_usage(per_cpu=True)
        "CPU Usage (Per Core):\\n  CPU 0: 30.0%\\n  CPU 1: 25.0%\\n  ..."
    """
    try:
        info = ["CPU Usage:\n"]

        # CPU count
        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        info.append(f"CPU Information:")
        info.append(f"  Physical Cores: {physical_cores}")
        info.append(f"  Logical Cores: {logical_cores}")

        # CPU usage
        if per_cpu:
            usage_per_cpu = psutil.cpu_percent(interval=interval, percpu=True)
            info.append("\nPer-Core Usage:")
            for i, usage in enumerate(usage_per_cpu):
                bar_length = 20
                filled = int(bar_length * usage / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                info.append(f"  CPU {i:2d}: {usage:5.1f}% [{bar}]")
        else:
            usage = psutil.cpu_percent(interval=interval)
            info.append(f"\nOverall Usage: {usage}%")

            bar_length = 20
            filled = int(bar_length * usage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            info.append(f"  Usage: [{bar}]")

        # CPU frequency
        try:
            freq = psutil.cpu_freq()
            if freq:
                info.append("\nCPU Frequency:")
                info.append(f"  Current: {freq.current:.2f} MHz")
                info.append(f"  Min: {freq.min:.2f} MHz")
                info.append(f"  Max: {freq.max:.2f} MHz")
        except Exception:
            pass  # CPU frequency not available on all platforms

        # Load average (Unix/Mac only)
        try:
            if hasattr(os, "getloadavg"):
                load1, load5, load15 = os.getloadavg()
                info.append("\nLoad Average:")
                info.append(f"  1 min:  {load1:.2f}")
                info.append(f"  5 min:  {load5:.2f}")
                info.append(f"  15 min: {load15:.2f}")
        except Exception:
            pass  # Load average not available on Windows

        # Top 5 CPU-consuming processes
        info.append("\nTop 5 CPU-Consuming Processes:")
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                # Get CPU percent with small interval for accuracy
                proc.cpu_percent(interval=0.1)
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage and get top 5
        processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
        for i, proc in enumerate(processes[:5], 1):
            info.append(
                f"  {i}. PID {proc['pid']:>6} | {proc['name']:<20} | {proc['cpu_percent']:.2f}%"
            )

        return "\n".join(info)

    except Exception as e:
        return f"Error: Failed to get CPU usage: {str(e)}"


# ===================================
# Shell Session Management
# ===================================

# Global dictionary to store active shell sessions
_shell_sessions: Dict[str, subprocess.Popen] = {}


@mcp.tool()
def create_shell_session(session_name: str, shell_path: Optional[str] = None) -> str:
    """
    Creates a persistent shell session for multi-step command execution.

    This function establishes an interactive shell session that maintains state
    across multiple commands. Useful for scenarios where you need to execute
    multiple related commands (e.g., cd followed by ls, or environment setup).

    Args:
        session_name (str): A unique identifier for the session. Used to reference
                           this session in subsequent execute_in_session calls.
                           Must be unique across all active sessions.
        shell_path (str, optional): Path to the shell executable. If None, uses
                                   the default shell for the platform:
                                   - Unix/Mac: /bin/bash or /bin/zsh
                                   - Windows: cmd.exe
                                   Examples: "/bin/zsh", "/bin/bash", "powershell"

    Returns:
        str: A message confirming session creation with session details, or an
             error message if:
             - Session name already exists
             - Shell path is invalid
             - Shell process failed to start

    Example:
        >>> create_shell_session("my_session", "/bin/bash")
        "Shell session 'my_session' created successfully.\\n  PID: 12345\\n  ..."
    """
    if session_name in _shell_sessions:
        return f"Error: Shell session '{session_name}' already exists. Use a different name or close the existing session first."

    try:
        # Determine default shell if not specified
        if shell_path is None:
            if platform.system() == "Windows":
                shell_path = "cmd.exe"
            else:
                # Try common shells
                for shell in ["/bin/zsh", "/bin/bash", "/bin/sh"]:
                    if os.path.exists(shell):
                        shell_path = shell
                        break
                if shell_path is None:
                    return "Error: No suitable shell found. Please specify shell_path explicitly."

        # Create the shell process
        process = subprocess.Popen(
            [shell_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        _shell_sessions[session_name] = process

        return (
            f"Shell session '{session_name}' created successfully.\n"
            f"  PID: {process.pid}\n"
            f"  Shell: {shell_path}\n"
            f"  Use execute_in_session('{session_name}', '<command>') to run commands."
        )

    except FileNotFoundError:
        return f"Error: Shell executable not found at '{shell_path}'."
    except Exception as e:
        return f"Error: Failed to create shell session: {str(e)}"


@mcp.tool()
def execute_in_session(session_name: str, command: str, timeout: int = 30) -> str:
    """
    Executes a command within an existing shell session.

    This function sends a command to a previously created shell session and
    returns the output. The session maintains its state (working directory,
    environment variables, etc.) between commands.

    Args:
        session_name (str): The name of the session to execute the command in.
                           Must have been created with create_shell_session.
        command (str): The command to execute in the shell. Can be any valid
                      shell command, including pipes, redirects, and multiple
                      commands separated by ; or &&.
        timeout (int): Maximum time to wait for command completion in seconds.
                      Defaults to 30. Commands that take longer will be terminated.

    Returns:
        str: The combined stdout and stderr output from the command, or an error
             message if:
             - Session does not exist
             - Session has terminated
             - Command execution fails
             - Timeout is exceeded

    Example:
        >>> execute_in_session("my_session", "cd /tmp && ls")
        "tmp_file1.txt\\ntmp_file2.txt\\n"
        >>> execute_in_session("my_session", "pwd")
        "/tmp\\n"
    """
    if session_name not in _shell_sessions:
        return f"Error: Shell session '{session_name}' not found. Use create_shell_session first."

    process = _shell_sessions[session_name]

    # Check if process is still running
    if process.poll() is not None:
        del _shell_sessions[session_name]
        return f"Error: Shell session '{session_name}' has terminated (PID: {process.pid})."

    try:
        # Send command
        cmd_with_newline = command + "\n"
        process.stdin.write(cmd_with_newline)
        process.stdin.flush()

        # Read output
        output_lines = []
        stderr_lines = []

        # Set a timeout for reading output
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                return f"Error: Command timed out after {timeout} seconds."

            # Check if there's data to read
            if process.stdout.readable():
                try:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(line)
                except:
                    pass

            # Note: This is a simplified implementation. In a production scenario,
            # you'd need more sophisticated output detection to know when the
            # command has finished (e.g., looking for prompt patterns)

            # For simplicity, we'll wait a short time and return what we have
            time.sleep(0.1)

            # Break after collecting some output or timeout
            if len(output_lines) > 0 and time.time() - start_time > 0.5:
                break

        output = "".join(output_lines)
        return output if output else f"Command '{command}' executed (no output captured)."

    except BrokenPipeError:
        del _shell_sessions[session_name]
        return f"Error: Shell session '{session_name}' has terminated unexpectedly."
    except Exception as e:
        return f"Error: Failed to execute command in session: {str(e)}"


@mcp.tool()
def close_session(session_name: str) -> str:
    """
    Closes an active shell session and releases its resources.

    This function terminates a shell session that was created with
    create_shell_session. The session will no longer be available for
    command execution after being closed.

    Args:
        session_name (str): The name of the session to close. Must be an
                           active session created with create_shell_session.

    Returns:
        str: A confirmation message if the session was closed successfully,
             or an error message if:
             - Session does not exist
             - Session has already terminated

    Example:
        >>> close_session("my_session")
        "Shell session 'my_session' closed successfully (PID: 12345)."
    """
    if session_name not in _shell_sessions:
        return f"Error: Shell session '{session_name}' not found."

    process = _shell_sessions[session_name]

    try:
        # Terminate the process
        pid = process.pid
        process.terminate()

        # Wait for process to terminate (max 3 seconds)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            process.wait()

        del _shell_sessions[session_name]

        return f"Shell session '{session_name}' closed successfully (PID: {pid})."

    except Exception as e:
        # Clean up from dictionary even if termination fails
        del _shell_sessions[session_name]
        return f"Shell session '{session_name}' closed with warnings: {str(e)}"


# ===================================
# Git Commands (Read-Only)
# ===================================


@mcp.tool()
def git_status(repo_path: str = ".") -> str:
    """
    Retrieves the current Git repository status showing changed and untracked files.

    This function executes 'git status' to display the working tree status,
    including modified, staged, and untracked files. Useful for quickly
    checking what has changed in a repository.

    Args:
        repo_path (str): Path to the Git repository. Defaults to "." (current directory).
                        Can be an absolute or relative path. The function will
                        change to this directory before running git commands.

    Returns:
        str: The git status output showing:
             - Current branch name
             - Changes to be committed (staged files)
             - Changes not staged (modified but not staged files)
             - Untracked files (not tracked by Git)
             - Or an error message if:
               - Not a Git repository
               - Git is not installed
               - Path does not exist

    Example:
        >>> git_status("./my-project")
        "On branch main\\nYour branch is up to date with 'origin/main'.\\n\\n..."
    """
    try:
        # Verify git is available
        if not shutil.which("git"):
            return "Error: Git is not installed or not in PATH."

        # Verify path exists
        if not os.path.exists(repo_path):
            return f"Error: Path '{repo_path}' does not exist."

        # Run git status
        result = subprocess.run(
            ["git", "status"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return result.stdout
        elif "not a git repository" in result.stderr.lower():
            return f"Error: '{repo_path}' is not a Git repository."
        else:
            return f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out."
    except Exception as e:
        return f"Error: Failed to get git status: {str(e)}"


@mcp.tool()
def git_diff(
    repo_path: str = ".", file_path: Optional[str] = None, staged: bool = False
) -> str:
    """
    Displays changes between commits, commit and working tree, etc.

    This function executes 'git diff' to show differences in files. Can show
    changes to specific files, staged changes, or all unstaged changes.

    Args:
        repo_path (str): Path to the Git repository. Defaults to "." (current directory).
        file_path (str, optional): Path to a specific file to show diff for.
                                  If None, shows diff for all changed files.
                                  Relative to repo_path.
        staged (bool): If True, shows diff of staged changes (git diff --staged).
                      If False, shows diff of unstaged changes.
                      Defaults to False.

    Returns:
        str: The unified diff output showing:
             - Lines added (prefixed with +)
             - Lines removed (prefixed with -)
             - Context lines (prefixed with space)
             - File headers with metadata
             - Or a message indicating no changes, or an error.

    Example:
        >>> git_diff(".", "src/main.py")
        "diff --git a/src/main.py b/src/main.py\\nindex 1234567..abcdef..."
        >>> git_diff(".", staged=True)
        "diff --git a/config.json b/config.json\\n..."
    """
    try:
        # Verify git is available
        if not shutil.which("git"):
            return "Error: Git is not installed or not in PATH."

        # Verify path exists
        if not os.path.exists(repo_path):
            return f"Error: Path '{repo_path}' does not exist."

        # Build git diff command
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")

        if file_path:
            cmd.append(file_path)

        # Run git diff
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            if result.stdout.strip():
                return result.stdout
            else:
                if staged:
                    return "No staged changes to display."
                else:
                    return "No unstaged changes to display."
        elif "not a git repository" in result.stderr.lower():
            return f"Error: '{repo_path}' is not a Git repository."
        else:
            return f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out."
    except Exception as e:
        return f"Error: Failed to get git diff: {str(e)}"


@mcp.tool()
def git_branch_info(repo_path: str = ".", show_all: bool = False) -> str:
    """
    Retrieves information about Git branches in the repository.

    This function displays branch information including the current branch,
    local branches, remote branches, and their relationships. Useful for
    understanding branch structure and status.

    Args:
        repo_path (str): Path to the Git repository. Defaults to "." (current directory).
        show_all (bool): If True, shows both local and remote tracking branches.
                        If False, shows only local branches.
                        Defaults to False.

    Returns:
        str: A formatted report containing:
             - Current branch (marked with *)
             - List of all local branches
             - Remote tracking branches (if show_all=True)
             - Branch relationships and commits
             - Or an error message if not a Git repository.

    Example:
        >>> git_branch_info(".")
        "Current branch: main\\n\\nLocal Branches:\\n  * main\\n    ..."
        >>> git_branch_info(".", show_all=True)
        "Current branch: feature-branch\\n\\nLocal Branches:\\n  * feature-branch\\n  ..."
    """
    try:
        # Verify git is available
        if not shutil.which("git"):
            return "Error: Git is not installed or not in PATH."

        # Verify path exists
        if not os.path.exists(repo_path):
            return f"Error: Path '{repo_path}' does not exist."

        info = []

        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            current_branch = result.stdout.strip()
            info.append(f"Current branch: {current_branch}\n")
        else:
            info.append("Current branch: Unable to determine\n")

        # Get list of branches
        cmd = ["git", "branch"]
        if show_all:
            cmd.append("-a")  # Show all branches (local and remote)

        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            if show_all:
                info.append("All Branches (local and remote):")
            else:
                info.append("Local Branches:")

            for line in result.stdout.split("\n"):
                if line.strip():
                    # Format: branches are prefixed with * for current
                    branch = line.strip()
                    if branch.startswith("*"):
                        info.append(f"  {branch} (current)")
                    else:
                        info.append(f"  {branch}")

            # Get remote info if available
            if not show_all:
                result_remote = subprocess.run(
                    ["git", "remote", "-v"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result_remote.returncode == 0 and result_remote.stdout.strip():
                    info.append("\nRemotes:")
                    for line in result_remote.stdout.strip().split("\n"):
                        info.append(f"  {line}")

            return "\n".join(info)
        elif "not a git repository" in result.stderr.lower():
            return f"Error: '{repo_path}' is not a Git repository."
        else:
            return f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out."
    except Exception as e:
        return f"Error: Failed to get git branch info: {str(e)}"


if __name__ == "__main__":
    mcp.run()
