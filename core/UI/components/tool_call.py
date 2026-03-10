"""
Tool Call UI component for displaying MCP tool calls.

This module provides ToolCallUI class for displaying tool execution
information in a visually appealing way using cyan/blue color scheme.
"""

from typing import Dict, Any
from core.UI.theme import ThemeColors
from core.UI.live import live


class ToolCallUI:
    """
    Helper class for displaying MCP tool calls with styled UI.

    This class provides methods to display tool execution information
    in a visually appealing way using cyan/blue color scheme.
    """

    def __init__(self, console):
        """
        Initialize the ToolCallUI.

        Args:
            console: Rich console instance for output
        """
        self.console = console

    def display_tool_call(self, tool_name: str) -> None:
        """
        Display tool call header.

        Args:
            tool_name: Name of the tool being called
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style

        header = Text()
        header.append("", style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))
        header.append("Tool Call: ", style=Style(color=ThemeColors.TOOL_SECONDARY))
        header.append(tool_name, style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))

        live.console.print(
            Panel(
                header,
                border_style=Style(color=ThemeColors.TOOL_BORDER),
                padding=(0, 1),
            )
        )

    def display_tool_input(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """
        Display tool input parameters.

        Args:
            tool_name: Full tool name
            arguments: Tool arguments dictionary
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        from rich.style import Style

        title = Text()
        title.append("📥 ", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Tool Input", style=Style(color=ThemeColors.TOOL_SECONDARY))

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style=Style(color=ThemeColors.TOOL_SECONDARY))
        table.add_column("Value", style=Style(color=ThemeColors.FG))

        table.add_row("Tool", tool_name)

        args_str = __import__("json").dumps(arguments, indent=2, ensure_ascii=False)
        table.add_row("Arguments", Text(args_str, style=Style(color=ThemeColors.DIM)))

        live.console.print(
            Panel(
                table,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )

    def display_execution_status(self, status: str = "executing") -> None:
        """
        Display tool execution status.

        Args:
            status: Either 'executing' or 'completed'
        """
        from rich.text import Text
        from rich.style import Style

        if status == "executing":
            status_text = Text()
            status_text.append("⟳ ", style=Style(color=ThemeColors.TOOL_ACCENT))
            status_text.append(
                "Executing...", style=Style(color=ThemeColors.TOOL_SECONDARY)
            )
        else:
            status_text = Text()
            status_text.append("✓ ", style=Style(color=ThemeColors.SUCCESS))
            status_text.append(
                "Completed", style=Style(color=ThemeColors.TOOL_SECONDARY)
            )

        live.console.print(status_text)

    def display_tool_result(self, result: str, max_length: int = 500) -> None:
        """
        Display tool execution result.

        Args:
            result: Result text from tool execution
            max_length: Maximum length to display before truncating
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style

        title = Text()
        title.append("📤 ", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Result", style=Style(color=ThemeColors.TOOL_SECONDARY))

        if len(result) > max_length:
            truncated = (
                result[:max_length]
                + f"...(truncated, full length: {len(result)} chars)"
            )
            result_text = Text(truncated, style=Style(color=ThemeColors.FG))
        else:
            result_text = Text(result, style=Style(color=ThemeColors.FG))

        live.console.print(
            Panel(
                result_text,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )
        live.console.print()

    def display_tool_error(self, error_msg: str) -> None:
        """
        Display tool execution error.

        Args:
            error_msg: Error message to display
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style

        error_text = Text()
        error_text.append("✗ ", style=Style(color=ThemeColors.ERROR))
        error_text.append(error_msg, style=Style(color=ThemeColors.ERROR))

        live.console.print(
            Panel(
                error_text,
                border_style=Style(color=ThemeColors.ERROR),
                padding=(0, 1),
            )
        )
        live.console.print()
