#!/usr/bin/env python3
"""
IntelliSearch Web API - Unified entry point for frontend and backend services.

This script starts both the Flask frontend and FastAPI backend services,
providing a complete web application.
"""

import sys
import os
import yaml
import time
import multiprocessing as mp
from pathlib import Path
from typing import Tuple

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from frontend.app import app, init_db
from frontend.app import init_config
from backend.web_backend import AsyncWebBackend
from config.config_loader import Config
from core.logger import get_logger, setup_logging
setup_logging(console_level="INFO")


def print_startup_success(backend_port: int, frontend_port: int):
    """
    Print success message after servers start using rich Panel.

    Args:
        backend_port: Backend server port
        frontend_port: Frontend server port
    """
    console = Console()

    # Print success message
    success_text = Text()
    success_text.append("", style="bold green")
    success_text.append("All servers started successfully", style="green")
    console.print(success_text)
    console.print()

    # Create table for service links
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Service", style="cyan", justify="left")
    table.add_column("URL", style="blue", justify="left")

    table.add_row("Frontend", f"http://localhost:{frontend_port}")
    table.add_row("Backend API", f"http://localhost:{backend_port}")
    table.add_row("API Docs", f"http://localhost:{backend_port}/docs")

    # Create panel with table
    panel = Panel(
        table,
        title="Access Your Services",
        title_align="left",
        border_style="bright_blue",
        padding=(1, 2),
    )

    console.print(panel)
    console.print()

    # Print control info
    info_text = Text()
    info_text.append("Press ", style="cyan")
    info_text.append("Ctrl+C", style="bold yellow")
    info_text.append(" to stop", style="cyan")
    console.print(info_text)
    console.print()


def load_agent_config(config_path: str) -> Tuple[str, dict]:
    """
    Load agent configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Tuple of (agent_type, agent_config)
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if "agent" not in config_data:
        raise ValueError(f"Missing 'agent' section in {config_path}")

    agent_config = config_data["agent"]

    # Load system prompt
    system_prompt_path = agent_config.get("system_prompt_path", None)
    if system_prompt_path:
        with open(system_prompt_path, "r", encoding="utf-8") as file:
            system_prompt = file.read()
    else:
        system_prompt = "You are a helpful assistant"

    # Build final configuration
    final_config = {
        "name": agent_config.get("name", "IntelliSearchAgent"),
        "model_name": agent_config.get("model_name", "deepseek-chat"),
        "max_tool_call": agent_config.get("max_tool_call", 5),
        "server_config_path": agent_config.get(
            "server_config_path", "config/config.yaml"
        ),
        "system_prompt": system_prompt,
    }

    # Add optional API configuration from environment
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    if base_url:
        final_config["base_url"] = base_url
    if api_key:
        final_config["api_key"] = api_key

    agent_type = agent_config.get("type", "mcp_base_agent")

    return agent_type, final_config


def run_backend(agent_type: str, agent_config: dict, host: str, port: int, config_path: str = "config/config.yaml"):
    """
    Run the FastAPI backend server.

    Args:
        agent_type: Type of agent to create
        agent_config: Agent configuration
        host: Server host
        port: Server port
        config_path: Path to configuration file
    """

    logger = get_logger(__name__, "backend")

    try:
        # Initialize Config in child process
        Config.reset_instance()
        config = Config(config_file_path=config_path)
        config.load_config(override=True)

        backend = AsyncWebBackend(
            agent_type=agent_type, agent_config=agent_config, host=host, port=port
        )
        logger.info(f"Backend server starting on http://{host}:{port}")
        backend.run()
    except Exception as e:
        logger.error(f"Backend error: {e}", exc_info=True)


def run_frontend(port: int, config_path: str = "config/config.yaml"):
    """
    Run the Flask frontend server.

    Args:
        port: Frontend server port
        config_path: Path to configuration file
    """

    logger = get_logger(__name__, "frontend")

    try:
        # Initialize Config in child process
        Config.reset_instance()

        # Initialize config using frontend's init_config function
        init_config(config_path)

        # Initialize database
        init_db()

        # Run Flask app
        logger.info(f"Frontend server starting on http://0.0.0.0:{port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Frontend error: {e}", exc_info=True)


def main():
    """
    Main entry point for the web application.

    Usage:
        python api.py [config_path] [--backend-port PORT] [--frontend-port PORT]

    Args:
        config_path: Optional path to YAML configuration file
                    Defaults to config/config.yaml
    """
    # Parse command line arguments
    config_path = "config/config.yaml"
    backend_port = 8001
    frontend_port = 50001

    # Parse args
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--backend-port" and i + 1 < len(sys.argv):
            backend_port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--frontend-port" and i + 1 < len(sys.argv):
            frontend_port = int(sys.argv[i + 1])
            i += 2
        elif not sys.argv[i].startswith("--"):
            config_path = sys.argv[i]
            i += 1
        else:
            i += 1

    logger = get_logger(__name__, "api")

    try:
        agent_type, agent_config = load_agent_config(config_path)

        # Set backend URL for frontend
        os.environ["BACKEND_URL"] = f"http://localhost:{backend_port}"

        # Create processes for frontend and backend
        backend_process = mp.Process(
            target=run_backend, args=(agent_type, agent_config, "0.0.0.0", backend_port, config_path)
        )

        frontend_process = mp.Process(target=run_frontend, args=(frontend_port, config_path))

        # Start both processes
        backend_process.start()
        frontend_process.start()

        # Display success message with prompt_toolkit
        time.sleep(2)
        print_startup_success(backend_port, frontend_port)

        # Wait for interrupt signal
        try:
            backend_process.join()
            frontend_process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down servers...")
            print("\n\nShutting down...")

            # Terminate processes
            backend_process.terminate()
            frontend_process.terminate()

            # Wait for cleanup
            backend_process.join(timeout=5)
            frontend_process.join(timeout=5)

            # Force kill if still running
            if backend_process.is_alive():
                backend_process.kill()
            if frontend_process.is_alive():
                frontend_process.kill()

            logger.info("Servers stopped")
            print("\nStopped successfully. Goodbye!\n")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nConfiguration Error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Set multiprocessing start method
    mp.set_start_method("spawn", force=True)
    main()
