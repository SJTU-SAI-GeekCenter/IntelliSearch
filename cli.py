#!/usr/bin/env python3
"""
IntelliSearch CLI - Interactive command-line interface for Agent inference.

This is the simplified entry point that delegates all logic to the backend layer.
"""

import sys
import os
import traceback
import yaml
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.style import Style

from ui.theme import ThemeColors
from backend.cli_backend import CLIBackend
from config.config_loader import Config


def print_logo(console: Console):
    """Display beautiful SAI-IntelliSearch logo with ASCII art."""
    logo_art = """
██╗███╗   ██╗████████╗███████╗██╗     ██╗     ██╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
██║████╗  ██║╚══██╔══╝██╔════╝██║     ██║     ██║██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
██║██╔██╗ ██║   ██║   █████╗  ██║     ██║     ██║███████╗█████╗  ███████║██████╔╝██║     ███████║
██║██║╚██╗██║   ██║   ██╔══╝  ██║     ██║     ██║╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
██║██║ ╚████║   ██║   ███████╗███████╗███████╗██║███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

    logo_text = Text()
    logo_text.append(logo_art, style=Style(color=ThemeColors.ACCENT, bold=True))

    logo_panel = Panel(
        logo_text,
        border_style=Style(color=ThemeColors.PRIMARY),
        padding=(1, 2),
        title="[bold]SJTU-SAI Geek Center[/bold]",
        title_align="right",
    )

    console.print(logo_panel)


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
        print("Warning: mcp_async_agent is not suitable for cli_frontend, use `mcp_base_agent` instead.")
        agent_type = "mcp_base_agent"

    return agent_type, final_config


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

    # Initialize console
    console = Console()

    try:
        # Initialize global Config singleton
        # This is required for backward compatibility with modules that use Config.get_instance()
        global_config = Config(config_file_path=config_path)
        global_config.load_config(override=True)

        # Load configuration
        agent_type, agent_config = load_agent_config(config_path)

        # Print logo
        print_logo(console)

        # Create and run CLI backend
        backend = CLIBackend(
            agent_type=agent_type, agent_config=agent_config, console=console
        )
        backend.run()

    except KeyboardInterrupt as e:
        console.print(Text(f"KEYBOARD INTERRUPT", style=Style(color="red")))
        sys.exit(0)

    except FileNotFoundError as e:
        console.print(Text(f"\nError: {e}", style=Style(color="red")))
        sys.exit(1)

    except ValueError as e:
        console.print(Text(f"\nConfiguration Error: {e}", style=Style(color="red")))
        sys.exit(1)

    except Exception as e:
        console.print(Text(f"\nFatal error: {e}", style=Style(color="red")))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
