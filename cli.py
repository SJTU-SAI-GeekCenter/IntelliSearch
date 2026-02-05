#!/usr/bin/env python3
"""
IntelliSearch CLI - Interactive command-line interface for Agent inference.

This module provides a user-friendly CLI for interacting with different
agent types through the AgentFactory, supporting multi-turn conversations,
MCP tool calls, and conversation management.
"""

import sys
import os
import yaml
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.style import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style as PromptStyle
from core.base import BaseAgent
from core.factory import AgentFactory
from core.schema import AgentRequest, AgentResponse
from core.logger import get_logger
from config.config_loader import Config

# Initialize global configuration and load environment variables
config = Config(config_file_path="config/config.yaml")
config.load_config(override=True)

# Import theme colors
from ui.theme import ThemeColors
from ui.tool_ui import ToolUIManager
from ui.status_manager import get_status_manager
from ui.loading_messages import get_random_processing_message


class IntelliSearchCLI:
    """
    Command-line interface for IntelliSearch Agent interactions.

    This class provides an interactive REPL (Read-Eval-Print Loop) for
    conversing with different agent types. It supports special commands
    for session management and configuration.

    Attributes:
        agent: Current agent instance
        agent_type: Type of agent being used
        agent_config: Configuration used to create the agent
        running: Control flag for the main loop
        console: Rich console instance for styled output

    Example:
        >>> cli = IntelliSearchCLI()
        >>> cli.run()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the CLI with default settings.

        Args:
            config_path: Path to YAML configuration file. If not provided,
                        uses default path: config/config.yaml
        """
        self.agent: Optional[any] = None
        self.agent_type: Optional[str] = None
        self.agent_config: dict = {}
        self.running: bool = False
        self.config_path = config_path or "config/config.yaml"
        self.logger = get_logger(__name__)

        # Initialize rich console with theme
        self.console = Console()

        # Setup tool UI manager with our console
        ToolUIManager.set_console(self.console)

        # Setup unified status manager
        self.status_manager = get_status_manager(self.console)

        # Setup prompt_toolkit session
        self._setup_prompt_session()

        # Available commands for auto-completion
        self.commands = [
            "help",
            "quit",
            "exit",
            "clear",
            "export",
            "config",
            "reset",
            "model",
            "max_tools",
        ]

        # Command completer
        self.command_completer = WordCompleter(
            self.commands, ignore_case=True, match_middle=True
        )

    def _setup_prompt_session(self):
        """Setup prompt_toolkit session with history and auto-suggestion."""
        history_path = Path.home() / ".intellisearch_history"

        # Custom style for prompt
        style = PromptStyle.from_dict(
            {
                "prompt": f"fg:{ThemeColors.ACCENT}",
                "input": f"fg:{ThemeColors.FG}",
            }
        )

        self.prompt_session = PromptSession(
            history=FileHistory(str(history_path)),
            auto_suggest=AutoSuggestFromHistory(),
            style=style,
            enable_history_search=True,
        )

    def load_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from YAML file with environment variable overrides.

        Returns:
            Configuration dictionary for agent creation

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {self.config_path}: {e}")

        if "agent" not in config_data:
            raise ValueError(f"Missing 'agent' section in {self.config_path}")

        agent_config = config_data["agent"]

        # Apply environment variable overrides
        env_overrides = {
            "type": os.getenv("AGENT_TYPE"),
            "name": os.getenv("AGENT_NAME"),
            "model_name": os.getenv("AGENT_MODEL_NAME"),
            "max_tool_call": os.getenv("AGENT_MAX_TOOL_CALL"),
            "server_config_path": os.getenv("AGENT_SERVER_CONFIG_PATH"),
        }

        for key, env_value in env_overrides.items():
            if env_value is not None:
                # Convert max_tool_call to int
                if key == "max_tool_call":
                    agent_config[key] = int(env_value)
                else:
                    agent_config[key] = env_value

        # Handle API configuration with environment variable overrides
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("BASE_URL")
        system_prompt_path = agent_config.get("system_prompt_path", None)
        if not system_prompt_path:
            self.logger.warning("System prompt not found.")
            self.system_prompt = "You are a helpful assistant"
        else:
            with open(system_prompt_path, "r", encoding="utf-8") as file:
                self.system_prompt = file.read()

        # Build final configuration
        final_config = {
            "name": agent_config.get("name", "IntelliSearchAgent"),
            "model_name": agent_config.get("model_name", "deepseek-chat"),
            "max_tool_call": agent_config.get("max_tool_call", 5),
            "server_config_path": agent_config.get(
                "server_config_path", "config/config.yaml"
            ),
            "system_prompt": self.system_prompt
        }

        # Add optional API configuration
        if base_url:
            final_config["base_url"] = base_url
        if api_key:
            final_config["api_key"] = api_key

        return agent_config.get("type", "mcp_base_agent"), final_config

    def print_sai_logo(self) -> None:
        """Display beautiful SAI-IntelliSearch logo with ASCII art."""
        logo_art = """
██╗███╗   ██╗████████╗███████╗██╗     ██╗     ██╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
██║████╗  ██║╚══██╔══╝██╔════╝██║     ██║     ██║██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
██║██╔██╗ ██║   ██║   █████╗  ██║     ██║     ██║███████╗█████╗  ███████║██████╔╝██║     ███████║
██║██║╚██╗██║   ██║   ██╔══╝  ██║     ██║     ██║╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
██║██║ ╚████║   ██║   ███████╗███████╗███████╗██║███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""
        # Apply theme color
        logo_text = Text()
        logo_text.append(logo_art, style=Style(color=ThemeColors.ACCENT, bold=True))

        # Combine
        full_logo = logo_text

        # Display in panel
        logo_panel = Panel(
            full_logo,
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(1, 2),
            title="[bold]SJTU-SAI Geek Center[/bold]",
            title_align="right",
        )

        self.console.print(logo_panel)

    def print_banner(self) -> None:
        """Display welcome banner and available agent types."""
        banner_text = Text()
        banner_text.append(
            "IntelliSearch", style=Style(color=ThemeColors.ACCENT, bold=True)
        )
        banner_text.append(
            " CLI v3.1", style=Style(color=ThemeColors.SECONDARY, bold=True)
        )
        banner_text.append(
            f"\nThe boundaries of searching capabilities are the boundaries of agents.",
            style=Style(color=ThemeColors.DIM),
        )
        banner_text.append(
            f"\nPowered by SJTU-SAI, GeekCenter.",
            style=Style(color=ThemeColors.DIM),
        )

        banner = Panel(
            banner_text,
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(1, 2),
        )

        self.console.print(banner)

        # Show available agent types
        available_types = AgentFactory.list_agent_types()
        types_text = Text()
        types_text.append("Available agents: ", style=Style(color=ThemeColors.DIM))
        types_text.append(
            ", ".join(available_types), style=Style(color=ThemeColors.ACCENT)
        )

        self.console.print(types_text)
        self.console.print(
            Text(
                "Type /help for a list of commands", style=Style(color=ThemeColors.DIM)
            )
        )
        self.console.print()

    def print_help(self) -> None:
        """Display help information for available commands."""
        help_table = Table(
            title="Available Commands",
            border_style=Style(color=ThemeColors.PRIMARY),
            header_style=Style(color=ThemeColors.ACCENT, bold=True),
            padding=(0, 1),
        )

        help_table.add_column("Command", style=Style(color=ThemeColors.FG))
        help_table.add_column("Description", style=Style(color=ThemeColors.DIM))

        commands_info = [
            ("/help", "Show this help message"),
            ("/quit or /exit", "Exit the CLI"),
            ("/clear", "Clear conversation history"),
            ("/export [path]", "Export conversation to JSON file"),
            ("/config", "Show current agent configuration"),
            ("/reset", "Reset agent with new configuration"),
            ("/model <name>", "Change LLM model (e.g., /model glm-4.5)"),
            ("/max_tools <n>", "Set max tool call iterations"),
        ]

        for cmd, desc in commands_info:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

        # Tips section
        tips_text = Text()
        tips_text.append("\nTips:\n", style=Style(color=ThemeColors.ACCENT, bold=True))
        tips = [
            "• Start a new session by running the CLI",
            "• Use /reset to reconfigure the agent",
            "• Use /export to save your conversation history",
            "• Use /clear to start a fresh conversation",
            "• Press Tab for command auto-completion",
            "• Use arrow keys to navigate command history",
        ]

        for tip in tips:
            tips_text.append(f"{tip}\n", style=Style(color=ThemeColors.DIM))

        self.console.print(tips_text)

    def setup_agent(self) -> bool:
        """
        Load configuration from file and create agent instance.

        Returns:
            True if agent was created successfully, False otherwise
        """

        try:
            # Load configuration from YAML file
            agent_type, config = self.load_config()

            # Validate agent type
            available_types = AgentFactory.list_agent_types()
            if agent_type not in available_types:
                self.console.print(Text(f"Error: Unknown agent type '{agent_type}'"))
                self.console.print(
                    Text(f"Available types: {', '.join(available_types)}")
                )
                return False

            self.agent: BaseAgent = AgentFactory.create_agent(
                agent_type=agent_type, **config
            )
            self.agent_type = agent_type
            self.agent_config = config
            return True

        except FileNotFoundError as e:
            self.console.print(
                Text(f"Error: {e}", style=Style(color=ThemeColors.ERROR))
            )
            self.logger.error(f"Configuration file not found: {e}")
            return False
        except ValueError as e:
            self.console.print(
                Text(f"Configuration Error: {e}", style=Style(color=ThemeColors.ERROR))
            )
            self.logger.error(f"Invalid configuration: {e}")
            return False
        except Exception as e:
            self.console.print(
                Text(f"Error creating agent: {e}", style=Style(color=ThemeColors.ERROR))
            )
            self.logger.error(f"Agent creation failed: {e}", exc_info=True)
            return False

    def parse_structured_response(
        self, response_text: str
    ) -> Optional[Tuple[str, str]]:
        """
        Parse structured response with final_response and tool_tracing tags.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Tuple of (final_response, tool_tracing) if both tags found,
            None if parsing fails
        """
        # Try to extract <final_response> tag
        final_response_match = re.search(
            r"<final_response>\s*(.*?)\s*</final_response>", response_text, re.DOTALL
        )

        # Try to extract <tool_tracing> tag
        tool_tracing_match = re.search(
            r"<tool_tracing>\s*(.*?)\s*</tool_tracing>", response_text, re.DOTALL
        )

        # Check if both tags are present
        if final_response_match and tool_tracing_match:
            final_response = final_response_match.group(1).strip()
            tool_tracing = tool_tracing_match.group(1).strip()
            return (final_response, tool_tracing)

        # If tags are not found, return None to indicate fallback needed
        return None

    def display_response(self, response: AgentResponse) -> None:
        """
        Display agent response with markdown rendering and metadata.

        Args:
            response: AgentResponse from agent inference
        """
        # Try to parse structured response
        parsed = self.parse_structured_response(response.answer)

        if parsed:
            # Successfully parsed - display in two separate panels
            final_response, tool_tracing = parsed

            # Display final response
            final_response_md = Markdown(
                final_response, style=Style(color=ThemeColors.FG)
            )
            final_response_panel = Panel(
                final_response_md,
                title="[bold]Final Response[/bold]",
                title_align="left",
                border_style=Style(color=ThemeColors.SECONDARY),
                padding=(0, 1),
            )
            self.console.print(final_response_panel)

            # Display tool tracing
            tool_tracing_md = Markdown(
                tool_tracing, style=Style(color=ThemeColors.FG)
            )
            tool_tracing_panel = Panel(
                tool_tracing_md,
                title="[bold dim]Tool Tracing[/bold dim]",
                title_align="left",
                border_style=Style(color=ThemeColors.PRIMARY),
                padding=(0, 1),
            )
            self.console.print(tool_tracing_panel)
            self.console.print()
        else:
            # Parse failed - fallback to original strategy
            # Create response panel with markdown
            response_md = Markdown(response.answer, style=Style(color=ThemeColors.FG))

            response_panel = Panel(
                response_md,
                title="IntelliSearch",
                title_align="left",
                border_style=Style(color=ThemeColors.SECONDARY),
                padding=(0, 1),
            )

            self.console.print(response_panel)
            self.console.print()

    def show_loading_indicator(self, message: str = "Processing"):
        """
        Display a loading spinner during agent inference.

        Args:
            message: Message to display next to spinner (if not provided, uses random message)
        """
        if message == "Processing":
            # Use random message from collection

            message = get_random_processing_message()
        self.status_manager.set_processing(message)

    def show_summarizing_indicator(self, message: str = "Generating final response..."):
        """
        Display a summarizing spinner during final response generation.

        Args:
            message: Message to display next to spinner (if not provided, uses random message)
        """
        if message == "Generating final response...":
            # Use random message from collection
            from ui.loading_messages import get_random_summarizing_message

            message = get_random_summarizing_message()
        self.status_manager.set_summarizing(message)

    def clear_loading_indicator(self):
        """Clear the loading indicator."""
        self.status_manager.clear()

    def get_user_input(self) -> str:
        """
        Get user input with styled prompt and auto-completion.

        Returns:
            User input string
        """
        # Use HTML-style formatting for prompt_toolkit
        prompt_text = [
            ("class:prompt", "You"),
            ("class:input", " › "),
        ]
        will_be_exited = False

        while True:
            try:
                user_input = self.prompt_session.prompt(
                    prompt_text,
                    completer=(
                        self.command_completer if self._detect_command_start() else None
                    ),
                )

                return user_input.strip()
            except KeyboardInterrupt:
                # Allow Ctrl+C to cancel input
                if will_be_exited:
                    self.console.print(
                        Text(
                            "\nExiting IntelliSearch CLI. Goodbye!\n",
                            style=Style(color=ThemeColors.ACCENT),
                        )
                    )
                    exit(0)
                else:
                    self.console.print(
                        "\n[red]Input cancelled. Press Ctrl+C again to exit.[/red]"
                    )
                    will_be_exited = True
                    continue

    def _detect_command_start(self) -> bool:
        """
        Detect if user is typing a command (starts with /).

        Returns:
            True if command is being typed, False otherwise
        """
        # This is a simplified check
        # In a real implementation, you might want to check the current buffer
        return False

    def process_command(self, command: str) -> bool:
        """
        Process special CLI commands with styled output.

        Args:
            command: Command string (without the '/' prefix)

        Returns:
            True to continue running, False to exit
        """
        cmd_parts = command.strip().split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""

        if cmd in ["quit", "exit"]:
            self.console.print(
                Text(
                    "\nExiting IntelliSearch CLI. Goodbye!\n",
                    style=Style(color=ThemeColors.ACCENT),
                )
            )
            return False

        elif cmd == "help":
            self.print_help()
            return True

        elif cmd == "clear":
            if self.agent:
                self.agent.clear_history()
                self.console.print(
                    Text(
                        "✓ Conversation history cleared.",
                        style=Style(color=ThemeColors.SUCCESS),
                    )
                )
                self.console.print()
            else:
                self.console.print(
                    Text(
                        "No active agent. Use /reset to create one.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                self.console.print()
            return True

        elif cmd == "export":
            if not self.agent:
                self.console.print(
                    Text(
                        "No active agent to export from.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                return True

            output_path = cmd_parts[1] if len(cmd_parts) > 1 else None
            try:
                result_path = self.agent.export_conversation(output_path)
                self.console.print(
                    Text(
                        f"✓ Conversation exported to: {result_path}",
                        style=Style(color=ThemeColors.SUCCESS),
                    )
                )
                self.console.print()
            except Exception as e:
                self.console.print(
                    Text(f"✗ Export failed: {e}", style=Style(color=ThemeColors.ERROR))
                )
                self.console.print()
            return True

        elif cmd == "config":
            if not self.agent:
                self.console.print(
                    Text(
                        "No active agent configured.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                return True

            # Create configuration table
            config_table = Table(
                title="Current Agent Configuration",
                border_style=Style(color=ThemeColors.PRIMARY),
                header_style=Style(color=ThemeColors.ACCENT, bold=True),
                padding=(0, 1),
            )

            config_table.add_column("Setting", style=Style(color=ThemeColors.FG))
            config_table.add_column("Value", style=Style(color=ThemeColors.DIM))

            config_table.add_row("Agent Type", str(self.agent_type))
            config_table.add_row("Agent Class", self.agent.__class__.__name__)

            for key, value in self.agent_config.items():
                if key == "api_key" and value:
                    value = "***HIDDEN***"
                config_table.add_row(key, str(value))

            self.console.print(config_table)
            self.console.print()
            return True

        elif cmd == "reset":
            self.console.print(
                Text(
                    "\n⟳ Resetting agent configuration...",
                    style=Style(color=ThemeColors.INFO),
                )
            )
            if self.setup_agent():
                self.console.print(
                    Text(
                        "✓ Agent reconfigured successfully.",
                        style=Style(color=ThemeColors.SUCCESS),
                    )
                )
                self.console.print()
            else:
                self.console.print(
                    Text(
                        "✗ Failed to reconfigure agent. Exiting.",
                        style=Style(color=ThemeColors.ERROR),
                    )
                )
                return False
            return True

        elif cmd == "model":
            if not self.agent:
                self.console.print(
                    Text(
                        "No active agent. Use /reset to create one.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                return True

            if len(cmd_parts) < 2:
                self.console.print(
                    Text(
                        f"Current model: {self.agent.model_name}",
                        style=Style(color=ThemeColors.INFO),
                    )
                )
                self.console.print(
                    Text(
                        "Usage: /model <model_name>", style=Style(color=ThemeColors.DIM)
                    )
                )
                return True

            new_model = cmd_parts[1]
            self.agent.model_name = new_model
            self.console.print(
                Text(
                    f"✓ Model changed to: {new_model}",
                    style=Style(color=ThemeColors.SUCCESS),
                )
            )
            self.console.print()
            return True

        elif cmd == "max_tools":
            if not self.agent:
                self.console.print(
                    Text(
                        "No active agent. Use /reset to create one.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                return True

            if len(cmd_parts) < 2 or not cmd_parts[1].isdigit():
                self.console.print(
                    Text(
                        f"Current max tool calls: {self.agent.max_tool_call}",
                        style=Style(color=ThemeColors.INFO),
                    )
                )
                self.console.print(
                    Text(
                        "Usage: /max_tools <number>", style=Style(color=ThemeColors.DIM)
                    )
                )
                return True

            new_max = int(cmd_parts[1])
            self.agent.max_tool_call = new_max
            self.console.print(
                Text(
                    f"✓ Max tool calls changed to: {new_max}",
                    style=Style(color=ThemeColors.SUCCESS),
                )
            )
            self.console.print()
            return True

        else:
            self.console.print(
                Text(f"Unknown command: /{cmd}", style=Style(color=ThemeColors.ERROR))
            )
            self.console.print(
                Text(
                    "Type /help for available commands",
                    style=Style(color=ThemeColors.DIM),
                )
            )
            self.console.print()
            return True

    def run(self) -> None:
        """
        Main CLI loop with enhanced UI.

        This method runs the interactive REPL until the user exits.
        """
        self.running = True

        # Display SAI logo
        self.print_sai_logo()

        # Display banner
        self.print_banner()

        # Setup agent
        if not self.setup_agent():
            self.console.print(
                Text(
                    "Failed to initialize agent. Exiting.",
                    style=Style(color=ThemeColors.ERROR),
                )
            )
            return

        while self.running:
            try:
                # Get user input with styled prompt
                user_input = self.get_user_input()

                if not user_input:
                    continue

                # Check for special commands
                if user_input.startswith("/"):
                    self.running = self.process_command(user_input[1:])
                    continue

                # Display user message in styled panel
                user_panel = Panel(
                    user_input,
                    title="You",
                    title_align="left",
                    border_style=Style(color=ThemeColors.PRIMARY),
                    padding=(0, 1),
                )
                self.console.print(user_panel)

                # Show loading and process request
                self.show_loading_indicator("Processing")
                try:
                    request = AgentRequest(prompt=user_input)
                    response = self.agent.inference(request)
                finally:
                    self.clear_loading_indicator()
                    # Print a newline to move past the status line
                    self.console.print()  # 确保换行

                # Display response with markdown rendering
                self.display_response(response)

            except KeyboardInterrupt:
                self.console.print("\n\n")
                self.console.print(
                    Text(
                        "⚠ Interrupted. Use /quit to exit.",
                        style=Style(color=ThemeColors.WARNING),
                    )
                )
                self.console.print()
                self.running = False
                continue

            except Exception as e:
                self.console.print(
                    Text(f"\n✗ Error: {e}", style=Style(color=ThemeColors.ERROR))
                )
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                self.running = False
                continue


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

    cli = IntelliSearchCLI(config_path=config_path)

    try:
        cli.run()
    except Exception as e:
        console = Console()
        console.print(Text(f"\n✗ Fatal error: {e}", style=Style(color="red")))
        sys.exit(1)


if __name__ == "__main__":
    main()
