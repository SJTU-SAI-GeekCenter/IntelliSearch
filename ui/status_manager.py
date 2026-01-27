"""
Unified Status Manager for CLI using Rich status.

This module provides a centralized status management system that uses
Rich's built-in status functionality to display status indicators.
"""

from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.style import Style

from .theme import ThemeColors


class StatusManager:
    """
    Unified status manager for CLI operations.

    This class ensures that all status indicators are displayed consistently
    using Rich's status() context manager for reliable rendering.
    """

    _instance: Optional["StatusManager"] = None
    _lock = object()  # Simple lock for singleton

    def __new__(cls, console: Optional[Console] = None):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the StatusManager.

        Args:
            console: Rich console instance
        """
        if self._initialized:
            return

        self.console = console or Console()
        self._active = False
        self._initialized = True

    def _get_status_text(self, message: str, icon: str, color: str) -> Text:
        """
        Get formatted status text.

        Args:
            message: Status message
            icon: Icon to display
            color: Color for icon

        Returns:
            Formatted Text object
        """
        status_text = Text()
        status_text.append(icon, style=Style(color=color, bold=True))
        status_text.append(f" {message}", style=Style(color=ThemeColors.SECONDARY))
        return status_text

    def set_processing(self, message: str = "Processing...") -> None:
        """
        Set processing status (for main LLM processing).

        Args:
            message: Status message to display
        """
        # Clear any existing console content on the current line
        import sys
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
        sys.stdout.flush()

        status_text = self._get_status_text(
            message, "⠋", ThemeColors.ACCENT
        )
        # Use print with end="" to keep on same line
        print(status_text.plain, end="", flush=True)
        self._active = True

    def set_executing(self, message: str = "Executing...") -> None:
        """
        Set executing status (for tool execution).

        Args:
            message: Status message to display
        """
        # Clear any existing console content on the current line
        import sys
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
        sys.stdout.flush()

        status_text = self._get_status_text(
            message, "⚙", ThemeColors.TOOL_ACCENT
        )
        # Use print with end="" to keep on same line
        print(status_text.plain, end="", flush=True)
        self._active = True

    def set_error(self, message: str = "Error") -> None:
        """
        Set error status.

        Args:
            message: Error message to display
        """
        # Clear any existing console content on the current line
        import sys
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
        sys.stdout.flush()

        status_text = self._get_status_text(
            message, "✗", ThemeColors.ERROR
        )
        print(status_text.plain, end="", flush=True)
        self._active = True

    def set_success(self, message: str = "Completed") -> None:
        """
        Set success status.

        Args:
            message: Success message to display
        """
        # Clear any existing console content on the current line
        import sys
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
        sys.stdout.flush()

        status_text = self._get_status_text(
            message, "✓", ThemeColors.SUCCESS
        )
        print(status_text.plain, end="", flush=True)
        self._active = True

    def clear(self) -> None:
        """Clear the status line."""
        if self._active:
            # Clear the line by printing spaces and moving cursor back
            import sys
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
            self._active = False

    def print_and_clear(self, content: str = "") -> None:
        """
        Print content and clear status line.

        Use this to print output while status is active.

        Args:
            content: Content to print
        """
        self.clear()
        if content:
            self.console.print(content)

    def finish(self) -> None:
        """Finish current status and clear the line."""
        self.clear()


# Global instance
_global_status: Optional[StatusManager] = None


def get_status_manager(console: Optional[Console] = None) -> StatusManager:
    """
    Get the global StatusManager instance.

    Args:
        console: Optional console to initialize with

    Returns:
        StatusManager instance
    """
    global _global_status
    if _global_status is None:
        _global_status = StatusManager(console)
    return _global_status
