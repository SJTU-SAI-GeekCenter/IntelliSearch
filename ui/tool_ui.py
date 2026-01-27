"""
Tool UI Manager for displaying MCP tool calls with styled output.

This module provides a singleton manager for displaying tool execution
information with a consistent visual style across the application.
"""

from typing import Optional, Dict, Any
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.style import Style

from .theme import ThemeColors


class ToolUIManager:
    """
    Singleton manager for displaying tool calls with styled UI.

    This class provides a centralized way to display tool execution
    information throughout the application.
    """

    _instance: Optional["ToolUIManager"] = None
    _console: Optional[Console] = None
    _enabled: bool = True

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._console = Console()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ToolUIManager":
        """
        Get the singleton instance of ToolUIManager.

        Returns:
            ToolUIManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_console(cls, console: Console) -> None:
        """
        Set the console instance for output.

        Args:
            console: Rich console instance
        """
        cls._console = console

    @classmethod
    def enable(cls) -> None:
        """Enable tool UI output."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable tool UI output."""
        cls._enabled = False

    def display_tool_call(self, tool_name: str) -> None:
        """
        Display tool call header.

        Args:
            tool_name: Name of the tool being called
        """
        if not self._enabled or not self._console:
            return

        # Clear any existing status before printing
        from .status_manager import get_status_manager
        status_mgr = get_status_manager()
        status_mgr.clear()
        self._console.print()  # Add newline after clearing status

        header = Text()
        header.append("", style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))
        header.append("Tool Call: ", style=Style(color=ThemeColors.TOOL_SECONDARY))
        header.append(tool_name, style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))

        self._console.print(
            Panel(
                header,
                border_style=Style(color=ThemeColors.TOOL_BORDER),
                padding=(0, 1),
            )
        )

    def display_tool_input(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> None:
        """
        Display tool input parameters.

        Args:
            tool_name: Full tool name
            arguments: Tool arguments dictionary
        """
        if not self._enabled or not self._console:
            return

        # Create title
        title = Text()
        title.append("", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Tool Input", style=Style(color=ThemeColors.TOOL_SECONDARY))

        # Create content table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style=Style(color=ThemeColors.TOOL_SECONDARY))
        table.add_column("Value", style=Style(color=ThemeColors.FG))

        table.add_row("Tool", tool_name)

        # Format arguments
        import json
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
        table.add_row("Arguments", Text(args_str, style=Style(color=ThemeColors.DIM)))

        self._console.print(
            Panel(
                table,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )

    def display_execution_status(self, status: str = "executing", message: str = "") -> None:
        """
        Display tool execution status using unified status manager.

        Args:
            status: Either 'executing' or 'completed'
            message: Optional status message
        """
        if not self._enabled:
            return

        from .status_manager import get_status_manager
        status_mgr = get_status_manager()

        if status == "executing":
            msg = message or "Executing tool..."
            status_mgr.set_executing(msg)
        elif status == "completed":
            msg = message or "Tool completed"
            status_mgr.set_success(msg)
            # Clear after a short delay
            import time
            time.sleep(0.3)
            status_mgr.clear()

    def display_tool_result(self, result: str, max_length: int = 500) -> None:
        """
        Display tool execution result.

        Args:
            result: Result text from tool execution
            max_length: Maximum length to display before truncating
        """
        if not self._enabled or not self._console:
            return

        # Clear any existing status before printing
        from .status_manager import get_status_manager
        status_mgr = get_status_manager()
        status_mgr.clear()
        self._console.print()  # Add newline after clearing status

        # Create title
        title = Text()
        title.append("", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Result", style=Style(color=ThemeColors.TOOL_SECONDARY))

        # Truncate if too long
        if len(result) > max_length:
            truncated = result[:max_length] + f"...(truncated, full length: {len(result)} chars)"
            result_text = Text(truncated, style=Style(color=ThemeColors.FG))
        else:
            result_text = Text(result, style=Style(color=ThemeColors.FG))

        self._console.print(
            Panel(
                result_text,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )
        self._console.print()

    def display_tool_error(self, error_msg: str) -> None:
        """
        Display tool execution error.

        Args:
            error_msg: Error message to display
        """
        if not self._enabled or not self._console:
            return

        # Clear any existing status before printing
        from .status_manager import get_status_manager
        status_mgr = get_status_manager()
        status_mgr.clear()
        self._console.print()  # Add newline after clearing status

        error_text = Text()
        error_text.append("✗ ", style=Style(color=ThemeColors.ERROR))
        error_text.append(error_msg, style=Style(color=ThemeColors.ERROR))

        self._console.print(
            Panel(
                error_text,
                border_style=Style(color=ThemeColors.ERROR),
                padding=(0, 1),
            )
        )
        self._console.print()


# Global instance
tool_ui = ToolUIManager()
