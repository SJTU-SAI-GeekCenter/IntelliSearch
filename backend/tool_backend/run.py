"""Tool Backend Services Manager.

This script manages multiple backend services using tmux:
- Creates a tmux session named 'tool_backend_services'
- Opens a separate window for each service
- Checks port availability before starting services
- Starts services using .venv Python interpreter

Usage:
    python backend/tool_backend/run.py           # Start all services
    python backend/tool_backend/run.py --stop    # Stop all services
    python backend/tool_backend/run.py --status  # Check service status
"""

import os
import sys
import subprocess
import time
import argparse
import socket
from pathlib import Path
from typing import List, Tuple

sys.path.append(os.getcwd())

from core.logger import get_logger
from config.config_loader import Config

logger = get_logger(__name__)
config = Config(config_file_path="config/config.yaml")
config.load_config(override=True)


class TmuxManager:
    """Manage tmux sessions and windows for backend services."""

    def __init__(self, session_name: str = "tool_backend_services"):
        """
        Initialize tmux manager.

        Args:
            session_name: Name of the tmux session
        """
        self.session_name = session_name

    def session_exists(self) -> bool:
        """
        Check if tmux session exists.

        Returns:
            True if session exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("tmux is not installed or not in PATH")
            return False

    def create_session(self) -> bool:
        """
        Create a new tmux session.

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", self.session_name],
                check=True,
                capture_output=True,
            )
            logger.info(f"Created tmux session: {self.session_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create tmux session: {e}")
            return False

    def kill_session(self) -> bool:
        """
        Kill the tmux session and all its windows.

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", self.session_name],
                check=True,
                capture_output=True,
            )
            logger.info(f"Killed tmux session: {self.session_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill tmux session: {e}")
            return False

    def create_window(self, window_name: str, command: str) -> bool:
        """
        Create a new window in the session and run a command.

        Args:
            window_name: Name for the window
            command: Command to run in the window

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create new window
            subprocess.run(
                [
                    "tmux",
                    "new-window",
                    "-t", self.session_name,
                    "-n", window_name,
                ],
                check=True,
                capture_output=True,
            )

            # Send command to the window
            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t", f"{self.session_name}:{window_name}",
                    command,
                    "C-m",
                ],
                check=True,
                capture_output=True,
            )

            logger.info(f"Created window '{window_name}' with command: {command}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create window '{window_name}': {e}")
            return False

    def list_windows(self) -> List[str]:
        """
        List all windows in the session.

        Returns:
            List of window names
        """
        try:
            result = subprocess.run(
                ["tmux", "list-windows", "-t", self.session_name, "-F", "#{window_name}"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError:
            return []


def check_port_available(port: int) -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check

    Returns:
        True if port is available, False if occupied
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return True
    except OSError:
        return False
    finally:
        sock.close()


def discover_services(directory: Path, config: Config) -> List[Tuple[str, int, str]]:
    """
    Discover all *_service.py files and their ports.

    Args:
        directory: Directory to search for service files
        config: Global configuration instance

    Returns:
        List of tuples (service_name, port, file_path)
    """
    services = []

    # Find all *_service.py files
    for service_file in directory.glob("*_service.py"):
        service_name = service_file.stem  # e.g., "rag_service"

        # Determine port from config
        if service_name == "rag_service":
            port_key = "tool_backend.rag_port"
        elif service_name == "ipython_service":
            port_key = "tool_backend.ipython_port"
        else:
            logger.warning(f"Unknown service: {service_name}, skipping")
            continue

        port = config.get_with_env(port_key, default=39257)
        services.append((service_name, port, str(service_file)))

    return services


def start_services(config):
    """Start all backend services in tmux."""
    logger.info("Starting backend services...")

    if not config.data:
        config = Config(config_file_path="config/config.yaml")
        config.load_config()

    # Initialize tmux manager
    tmux = TmuxManager()

    # Check if session already exists
    if tmux.session_exists():
        logger.warning(f"tmux session '{tmux.session_name}' already exists")
        response = input("Do you want to kill it and restart? (y/N): ")
        if response.lower() == "y":
            if not tmux.kill_session():
                logger.error("Failed to kill existing session")
                return
        else:
            logger.info("Exiting without making changes")
            return

    # Create new session
    if not tmux.create_session():
        logger.error("Failed to create tmux session")
        return

    # Discover services
    tool_backend_dir = Path(__file__).parent
    services = discover_services(tool_backend_dir, config)

    if not services:
        logger.warning("No services found to start")
        return

    logger.info(f"Found {len(services)} service(s)")

    # Start each service
    for service_name, port, service_file in services:
        logger.info(f"\nChecking port {port} for {service_name}...")

        # Check port availability
        if not check_port_available(port):
            logger.error(f"Port {port} is already in use, skipping {service_name}")
            continue

        # Get Python interpreter path
        venv_python = Path.cwd() / ".venv" / "bin" / "python"
        if not venv_python.exists():
            logger.error(f"Python interpreter not found: {venv_python}")
            continue

        # Construct command
        relative_path = Path(service_file).relative_to(Path.cwd())
        command = f"{venv_python} {relative_path}"

        # Create tmux window
        if tmux.create_window(service_name, command):
            logger.info(f"✓ Started {service_name} on port {port}")
        else:
            logger.error(f"✗ Failed to start {service_name}")

    # Wait a bit for services to start
    time.sleep(2)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Services started successfully!")
    logger.info("=" * 60)
    logger.info(f"\nTo attach to the session:")
    logger.info(f"  tmux attach-session -t {tmux.session_name}")
    logger.info(f"\nTo list windows:")
    logger.info(f"  tmux list-windows -t {tmux.session_name}")
    logger.info(f"\nTo detach from session: Ctrl+B, then D")
    logger.info(f"\nTo kill session:")
    logger.info(f"  python {Path(__file__)} --stop")


def stop_services(config):
    """Stop all backend services by killing the tmux session."""
    logger.info("Stopping backend services...")

    tmux = TmuxManager()

    if not tmux.session_exists():
        logger.warning(f"tmux session '{tmux.session_name}' does not exist")
        return

    if tmux.kill_session():
        logger.info("✓ All services stopped")
    else:
        logger.error("✗ Failed to stop services")


def show_status(config):
    """Show status of all backend services."""
    logger.info("Checking backend services status...")

    # Load config (using singleton pattern)
    config = Config.get_instance()
    if not config.data:
        config = Config(config_file_path="config/config.yaml")
        config.load_config()

    # Discover services
    tool_backend_dir = Path(__file__).parent
    services = discover_services(tool_backend_dir, config)

    if not services:
        logger.warning("No services found")
        return

    logger.info("\n" + "=" * 60)
    logger.info("Service Status:")
    logger.info("=" * 60)

    # Check each service
    running_count = 0
    for service_name, port, _ in services:
        if check_port_available(port):
            status = "❌ Stopped"
        else:
            status = "✓ Running"
            running_count += 1

        logger.info(f"  {service_name:20} (port {port}): {status}")

    logger.info("=" * 60)
    logger.info(f"Total: {running_count}/{len(services)} services running")
    logger.info("=" * 60)

    # Check tmux session
    tmux = TmuxManager()
    if tmux.session_exists():
        logger.info(f"\ntmux session '{tmux.session_name}' exists")
        logger.info(f"Windows: {', '.join(tmux.list_windows())}")
        logger.info(f"\nAttach with: tmux attach-session -t {tmux.session_name}")
    else:
        logger.info(f"\ntmux session '{tmux.session_name}' does not exist")


def main(config):
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Manage backend services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start all services
  python backend/tool_backend/run.py

  # Stop all services
  python backend/tool_backend/run.py --stop

  # Check service status
  python backend/tool_backend/run.py --status

  # Restart services
  python backend/tool_backend/run.py --stop && python backend/tool_backend/run.py
        """,
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all services by killing tmux session",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of all services",
    )

    args = parser.parse_args()

    if args.status:
        show_status(config=config)
    elif args.stop:
        stop_services(config=config)
    else:
        start_services(config=config)


if __name__ == "__main__":
    main(config=config)
