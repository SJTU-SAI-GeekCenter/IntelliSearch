"""
CLI backend implementation for IntelliSearch.

This module provides the CLI-specific UI implementation that connects
the CLIService to Rich console output.
"""

import re
from typing import Optional, Tuple
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
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style as PromptStyle
from pathlib import Path

from services.cli_service import CLIService
from core.schema import AgentRequest, AgentResponse
from core.logger import get_logger
from ui.theme import ThemeColors
from ui.status_manager import get_status_manager
from ui.tool_ui import ToolUIManager


class CLIBackend:
    """
    CLI backend that orchestrates the CLI user experience.

    This class connects the service layer with Rich UI components, handling:
    - User input via prompt_toolkit
    - Rich console output rendering
    - Status indicators and loading states
    - Command processing
    - Error display

    Attributes:
        service: The CLIService instance
        console: Rich console for output
        status_manager: Unified status manager for UI updates
        running: Control flag for main loop

    Example:
        >>> backend = CLIBackend(
        ...     agent_type="mcp_base_agent",
        ...     agent_config={"model_name": "deepseek-chat"}
        ... )
        >>> backend.run()
    """

    def __init__(
        self, agent_type: str, agent_config: dict, console: Optional[Console] = None
    ):
        """
        Initialize the CLI backend.

        Args:
            agent_type: Type of agent to create
            agent_config: Configuration for agent creation
            console: Optional Rich console (defaults to new Console())
        """
        self.logger = get_logger(__name__, "cli_backend")
        self.console = console or Console()
        self.running = False
        self.cancel_requested = False  # ESC 取消标志

        # Initialize service
        self.service = CLIService(agent_type, agent_config)

        # Setup UI components
        ToolUIManager.set_console(self.console)
        self.status_manager = get_status_manager(self.console)

        # Register status callback to bridge service -> UI
        self.service.register_status_callback(self._handle_status_update)

        # Setup prompt session
        self._setup_prompt_session()

        # Available commands
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
        self.command_completer = WordCompleter(
            self.commands, ignore_case=True, match_middle=True
        )

        self.logger.info("CLI backend initialized")

    def _setup_prompt_session(self):
        """Setup prompt_toolkit session with history and auto-suggestion."""

        history_path = Path.home() / ".intellisearch_history"

        # Create custom key bindings
        kb = KeyBindings()

        @kb.add(Keys.Escape)
        def _(event):
            """Handle ESC key to cancel current input."""
            # 使用预先定义的特殊标记来表示取消
            event.app.exit(result="\x03")  # 使用 ETX (End of Text) 字符作为取消标记

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
            key_bindings=kb,
        )

    def _handle_status_update(self, status_type: str, message: str):
        """
        Handle status updates from the service layer.

        This callback bridges service-level status changes to Rich UI updates.

        Args:
            status_type: Type of status ("processing", "summarizing", "clear", etc.)
            message: Status message
        """
        if status_type == "processing":
            if self.status_manager:
                self.status_manager.set_processing(message)
        elif status_type == "summarizing":
            if self.status_manager:
                self.status_manager.set_summarizing(message)
        elif status_type == "warning":
            # Display warning in a styled panel
            if self.status_manager:
                self.status_manager.clear()
            warning_text = Text(message, style=Style(color=ThemeColors.FG))

            warning_panel = Panel(
                warning_text,
                title="[bold]Warning[/bold]",
                title_align="left",
                border_style=Style(color=ThemeColors.WARNING),
                padding=(0, 1),
            )
            self.console.print(warning_panel)
        elif status_type == "clear":
            if self.status_manager:
                self.status_manager.clear()
        elif status_type == "error":
            if self.status_manager:
                self.status_manager.clear()
            self.console.print(
                Text(f"Error: {message}", style=Style(color=ThemeColors.ERROR))
            )
        elif status_type == "info":
            self.console.print(
                Text(f"Info: {message}", style=Style(color=ThemeColors.INFO))
            )
        elif status_type == "failed":
            if self.status_manager:
                self.status_manager.clear()

    def print_banner(self):
        """Display welcome banner."""
        banner_text = Text()
        banner_text.append(
            "IntelliSearch", style=Style(color=ThemeColors.ACCENT, bold=True)
        )
        banner_text.append(
            " CLI v3.2", style=Style(color=ThemeColors.SECONDARY, bold=True)
        )
        banner_text.append(
            "\nThe boundaries of searching capabilities are the boundaries of agents.",
            style=Style(color=ThemeColors.DIM),
        )
        banner_text.append(
            "\nPowered by SJTU-SAI, GeekCenter.", style=Style(color=ThemeColors.DIM)
        )

        banner = Panel(
            banner_text,
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(1, 2),
        )

        self.console.print(banner)

        agent_info = self.service.get_agent_info()
        info_text = Text()
        info_text.append("Agent: ", style=Style(color=ThemeColors.DIM))
        info_text.append(
            f"{agent_info['class']} ({agent_info['type']})",
            style=Style(color=ThemeColors.ACCENT),
        )

        self.console.print(info_text)
        self.console.print(
            Text(
                "Type /help for a list of commands", style=Style(color=ThemeColors.DIM)
            )
        )
        self.console.print()

    def print_help(self):
        """Display help information."""
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
            ("/model <name>", "Change LLM model"),
            ("/max_tools <n>", "Set max tool call iterations"),
        ]

        for cmd, desc in commands_info:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

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

    def display_response(self, response: AgentResponse):
        """
        Display agent response with markdown rendering and metadata.

        Args:
            response: AgentResponse from service
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
            tool_tracing_md = Markdown(tool_tracing, style=Style(color=ThemeColors.FG))
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

    def get_user_input(self) -> Optional[str]:
        """
        Get user input with styled prompt.

        Returns:
            User input string, or None if ESC was pressed to cancel current input
        """
        prompt_text = [
            ("class:prompt", "You"),
            ("class:input", " › "),
        ]

        try:
            user_input: str = self.prompt_session.prompt(
                prompt_text,
                completer=(
                    self.command_completer if self._detect_command_start() else None
                ),
            )

            return user_input.strip()

        except KeyboardInterrupt:
            raise

    def _detect_command_start(self) -> bool:
        """Detect if user is typing a command (starts with /)."""
        return False

    def process_command(self, command: str) -> bool:
        """
        Process special CLI commands.

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
            self.service.clear_agent_history()
            self.console.print(
                Text(
                    "Conversation history cleared.",
                    style=Style(color=ThemeColors.SUCCESS),
                )
            )
            self.console.print()
            return True

        elif cmd == "export":
            output_path = cmd_parts[1] if len(cmd_parts) > 1 else None
            try:
                result_path = self.service.export_conversation(output_path)
                self.console.print(
                    Text(
                        f"Conversation exported to: {result_path}",
                        style=Style(color=ThemeColors.SUCCESS),
                    )
                )
                self.console.print()
            except Exception as e:
                self.console.print(
                    Text(f"Export failed: {e}", style=Style(color=ThemeColors.ERROR))
                )
                self.console.print()
            return True

        elif cmd == "config":
            self._show_config()
            return True

        elif cmd == "model":
            if len(cmd_parts) < 2:
                self.console.print(
                    Text(
                        f"Current model: {self.service.agent.model_name}",
                        style=Style(color=ThemeColors.INFO),
                    )
                )
                return True

            new_model = cmd_parts[1]
            self.service.update_agent_config(model_name=new_model)
            self.console.print(
                Text(
                    f"Model changed to: {new_model}",
                    style=Style(color=ThemeColors.SUCCESS),
                )
            )
            self.console.print()
            return True

        elif cmd == "max_tools":
            if len(cmd_parts) < 2 or not cmd_parts[1].isdigit():
                self.console.print(
                    Text(
                        f"Current max tools: {self.service.agent.max_tool_call}",
                        style=Style(color=ThemeColors.INFO),
                    )
                )
                return True

            new_max = int(cmd_parts[1])
            self.service.update_agent_config(max_tool_call=new_max)
            self.console.print(
                Text(
                    f"Max tools changed to: {new_max}",
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

    def _show_config(self):
        """Display current agent configuration."""
        config_table = Table(
            title="Current Agent Configuration",
            border_style=Style(color=ThemeColors.PRIMARY),
            header_style=Style(color=ThemeColors.ACCENT, bold=True),
            padding=(0, 1),
        )

        config_table.add_column("Setting", style=Style(color=ThemeColors.FG))
        config_table.add_column("Value", style=Style(color=ThemeColors.DIM))

        agent_info = self.service.get_agent_info()
        config_table.add_row("Agent Type", agent_info["type"])
        config_table.add_row("Agent Class", agent_info["class"])
        config_table.add_row("Agent Name", agent_info["name"])

        if hasattr(self.service.agent, "model_name"):
            config_table.add_row("Model", self.service.agent.model_name)
        if hasattr(self.service.agent, "max_tool_call"):
            config_table.add_row("Max Tools", str(self.service.agent.max_tool_call))

        self.console.print(config_table)
        self.console.print()

    def run(self):
        """
        Main CLI loop.

        This method runs the interactive REPL until the user exits.
        """
        self.running = True
        self.cancel_requested = False

        # Display banner
        self.print_banner()

        # Main loop
        while self.running:
            try:
                user_input = self.get_user_input()
                # Handle ESC key (returns None)
                if user_input is None or user_input == "^[":
                    self.console.print(
                        Text("[Cancelled]", style=Style(color=ThemeColors.DIM))
                    )
                    self.console.print()
                    continue

                # Handle empty input
                if not user_input:
                    continue

                # Check for special commands
                if user_input.startswith("/"):
                    self.running = self.process_command(user_input[1:])
                    continue

                # Display user message
                user_panel = Panel(
                    user_input,
                    title="You",
                    title_align="left",
                    border_style=Style(color=ThemeColors.PRIMARY),
                    padding=(0, 1),
                )
                self.console.print(user_panel)

                # Process request - allow interruption via Ctrl+C
                try:
                    request = AgentRequest(prompt=user_input)
                    response = self.service.process_request_sync(request)
                    self.display_response(response)

                except KeyboardInterrupt:
                    try:
                        if self.status_manager:
                            self.status_manager.clear()
                    except:
                        pass

                    self.console.print()
                    self.console.print(
                        Text(
                            "Operation cancelled.",
                            style=Style(color=ThemeColors.WARNING),
                        )
                    )
                    self.console.print()
                    continue

                except Exception as e:
                    try:
                        if self.status_manager:
                            self.status_manager.clear()
                    except:
                        pass

                    self.console.print()
                    self.console.print(
                        Text(f"Error: {e}", style=Style(color=ThemeColors.ERROR))
                    )
                    self.logger.error(f"Request error: {e}", exc_info=True)

            except KeyboardInterrupt:
                self.console.print("\n\n")
                self.console.print(
                    Text(
                        "Exiting IntelliSearch CLI. Goodbye!",
                        style=Style(color=ThemeColors.ACCENT),
                    )
                )
                self.console.print()
                self.running = False
                break

            except Exception as e:
                self.console.print(
                    Text(
                        f"\nUnexpected error: {e}", style=Style(color=ThemeColors.ERROR)
                    )
                )
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                self.running = False
