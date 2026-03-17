#!/usr/bin/env python3
"""
IntelliSearch CLI - Interactive command-line interface for Agent inference.

This is simplified entry point that delegates all logic to backend layer.
"""

import sys
import os
import traceback
import yaml
import asyncio
import logging
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.style import Style

from core.UI import UIEngine
from core.UI.console import console
from backend.cli_backend import CLIBackend
from config.config_loader import Config
from core.exceptions import IntelliSearchError

# Suppress asyncio error logs for unhandled exceptions during Ctrl+C
# This prevents "Task exception was never retrieved" messages
logging.getLogger("asyncio").setLevel(logging.CRITICAL)


# Set global asyncio exception handler to suppress all unhandled exceptions
# This prevents "Unhandled exception in event loop" messages
def suppress_asyncio_exception(loop, context):
    """Suppress all asyncio exceptions to prevent error output."""
    pass  # Do nothing - suppress all exceptions


# Apply the exception handler to the current event loop
try:
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(suppress_asyncio_exception)
except RuntimeError:
    # No event loop yet - will be set when loop is created
    pass


def load_agent_config(config_path: str) -> tuple:
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
    # * cli is not async, thus mcp_async_agent is forbidden
    if agent_type == "mcp_async_agent":
        print(
            "Warning: mcp_async_agent is not suitable for cli_frontend, use `mcp_base_agent` instead."
        )
        agent_type = "mcp_base_agent"

    return agent_type, final_config


def cleanup_async_tasks():
    """
    Clean up all asyncio tasks to prevent 'Task exception was never retrieved' errors.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop and not loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()

            # Give tasks a chance to clean up
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
    except:
        pass  # Ignore errors during cleanup


def main():
    """
    Entry point for the CLI.

    Usage:
        python cli.py [config_path]

    Args:
        config_path: Optional path to YAML configuration file.
                    Defaults to config/config.yaml if not provided.
    """
    # Parse command line arguments
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"

    try:
        # Initialize global Config singleton
        # This is required for backward compatibility with modules that use Config.get_instance()
        global_config = Config(config_file_path=config_path)
        global_config.load_config(override=True)

        # Load configuration
        agent_type, agent_config = load_agent_config(config_path)

        # Display welcome message using WelcomeUI component
        welcome_ui = UIEngine.get_welcome_ui()
        welcome_ui.display_full_welcome()

        # Create and run CLI backend
        backend = CLIBackend(agent_type=agent_type, agent_config=agent_config)
        backend.run()

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        console.print("\n[bold red]程序已通过 Ctrl+C 终止[/bold red]")
        cleanup_async_tasks()
        sys.exit(0)

    except FileNotFoundError as e:
        console.print(Text(f"\nError: {e}", style=Style(color="red")))
        sys.exit(1)

    except IntelliSearchError as e:
        # Handle IntelliSearch errors with UI display
        UIEngine.display_exception(e)
        # Exit based on error severity
        if e.severity.value in ["FATAL", "CRITICAL"]:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        # Handle unknown errors
        console.print(Text(f"\nFatal error: {e}", style=Style(color="red")))
        traceback.print_exc()
        cleanup_async_tasks()
        sys.exit(1)


if __name__ == "__main__":
    main()
