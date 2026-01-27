"""
Output Manager for unified display with status bar.

This module provides a centralized output management system that uses
Rich Live display to show content with a unified status bar at the bottom.
"""

from typing import List, Optional, Any
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.align import Align
from rich.table import Table
from rich.style import Style
from rich.rule import Rule

from .theme import ThemeColors


class OutputManager:
    """
    Unified output manager with status bar.

    This class manages all output display with a fixed status bar at the bottom
    of the screen, preventing conflicts between multiple status indicators.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the OutputManager.

        Args:
            console: Rich console instance (creates new one if None)
        """
        self.console = console or Console()

        # Content lines to display
        self.content_lines: List[Any] = []

        # Current status
        self.current_status: Optional[str] = None
        self.status_type: str = "idle"  # idle, processing, executing, error, success

        # Live display
        self.live: Optional[Live] = None

    def _get_status_text(self) -> Text:
        """
        Get formatted status text for the status bar.

        Returns:
            Text object with formatted status
        """
        status_text = Text()

        if self.status_type == "processing":
            status_text.append("⠋ ", style=Style(color=ThemeColors.ACCENT))
            status_text.append(self.current_status or "Processing...",
                             style=Style(color=ThemeColors.SECONDARY))
        elif self.status_type == "executing":
            status_text.append("⚙ ", style=Style(color=ThemeColors.TOOL_ACCENT))
            status_text.append(self.current_status or "Executing...",
                             style=Style(color=ThemeColors.TOOL_SECONDARY))
        elif self.status_type == "error":
            status_text.append("✗ ", style=Style(color=ThemeColors.ERROR))
            status_text.append(self.current_status or "Error",
                             style=Style(color=ThemeColors.ERROR))
        elif self.status_type == "success":
            status_text.append("✓ ", style=Style(color=ThemeColors.SUCCESS))
            status_text.append(self.current_status or "Completed",
                             style=Style(color=ThemeColors.SECONDARY))
        else:
            # Idle
            status_text.append("●", style=Style(color=ThemeColors.DIM))
            status_text.append(" Ready",
                             style=Style(color=ThemeColors.DIM))

        return status_text

    def _get_display_content(self) -> Any:
        """
        Get the complete display content including status bar.

        Returns:
            Layout or renderable object for Live display
        """
        # Create layout
        layout = Layout()

        # Split into main content and status bar
        layout.split_column(
            Layout(name="main", ratio=1),
            Layout(name="status", size=1),
        )

        # Main content area
        if self.content_lines:
            # Display all content lines
            from rich.console import Group
            layout["main"].update(Group(*self.content_lines))
        else:
            # Empty state
            layout["main"].update(
                Align.center(
                    Text("IntelliSearch CLI", style=Style(color=ThemeColors.DIM))
                )
            )

        # Status bar at bottom
        status_panel = Panel(
            Align.center(self._get_status_text()),
            border_style=Style(color=ThemeColors.DIM),
            padding=(0, 1),
        )
        layout["status"].update(status_panel)

        return layout

    def start(self) -> None:
        """Start the live display."""
        if self.live is None:
            self.live = Live(
                self._get_display_content(),
                console=self.console,
                refresh_per_second=4,
            )
            self.live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self.live is not None:
            self.live.stop()
            self.live = None

    def update(self) -> None:
        """Update the display content."""
        if self.live is not None:
            self.live.update(self._get_display_content())

    def set_status(self, status: str, status_type: str = "processing") -> None:
        """
        Set the current status message.

        Args:
            status: Status message to display
            status_type: Type of status (idle, processing, executing, error, success)
        """
        self.current_status = status
        self.status_type = status_type
        self.update()

    def clear_status(self) -> None:
        """Clear the current status and return to idle."""
        self.current_status = None
        self.status_type = "idle"
        self.update()

    def add_content(self, content: Any) -> None:
        """
        Add content to the main display area.

        Args:
            content: Rich renderable object (Panel, Text, Table, etc.)
        """
        self.content_lines.append(content)
        self.update()

    def clear_content(self) -> None:
        """Clear all content from the main display area."""
        self.content_lines.clear()
        self.update()

    def print(self, *args, **kwargs) -> None:
        """
        Print directly to console (bypasses Live display).

        Use this for final output after stopping Live display.

        Args:
            *args: Arguments to pass to console.print
            **kwargs: Keyword arguments to pass to console.print
        """
        self.console.print(*args, **kwargs)


# Global instance
_output_manager: Optional[OutputManager] = None


def get_output_manager(console: Optional[Console] = None) -> OutputManager:
    """
    Get the global OutputManager instance.

    Args:
        console: Optional console to initialize with

    Returns:
        OutputManager instance
    """
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager(console)
    return _output_manager
