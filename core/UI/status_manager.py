"""
Unified Status Manager for CLI with dynamic animations.

This module provides a centralized status management system with
animated status panels using Rich Live display.
"""

import time
import threading
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from core.UI.live import (
    live,
    start_live,
    stop_live,
    set_live_layer,
    clear_live_layer,
    has_live_layers,
)
from core.UI.console import console
from .theme import ThemeColors


class StatusManager:
    """
    Unified status manager with animated displays.

    This class provides animated status indicators using Rich's Live display
    for a modern, dynamic user experience.
    """

    _instance: Optional["StatusManager"] = None
    _lock = object()

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the StatusManager.

        """
        if self._initialized:
            return
        self._current_status = None
        self._status_type = "idle"
        self._spinner_frame = 0
        self._active = False
        self._initialized = True

        # Spinner characters for animation
        self._spinner_dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_arrows = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
        self._spinner_stars = ["✶", "✷", "✸", "✹", "✺", "✴", "✳", "✲"]
        self._current_spinner = self._spinner_dots

        # Animation thread management
        self._animation_thread = None
        self._stop_event = threading.Event()  # Signal to stop animation

    def _get_spinner_char(self) -> str:
        """Get current spinner character."""
        char = self._current_spinner[self._spinner_frame]
        self._spinner_frame = (self._spinner_frame + 1) % len(self._current_spinner)
        return char

    def _get_status_panel(self) -> Panel:
        """Get the status panel for display."""
        if self._status_type == "idle" or not self._current_status:
            return Panel("")

        spinner = self._get_spinner_char()

        if self._status_type == "processing":
            # Green theme for processing
            title = Text()
            title.append(
                spinner + " ", style=Style(color=ThemeColors.ACCENT, bold=True)
            )
            title.append("PROCESSING", style=Style(color=ThemeColors.ACCENT, bold=True))

            content = Text()
            content.append(self._current_status, style=Style(color=ThemeColors.FG))

            return Panel(
                content,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.ACCENT),
                padding=(0, 2),  # Reduced vertical padding
                expand=True,  # Expand to full width
            )

        elif self._status_type == "executing":
            # Cyan theme for tool execution
            title = Text()
            title.append(
                spinner + " ", style=Style(color=ThemeColors.TOOL_ACCENT, bold=True)
            )
            title.append(
                "EXECUTING TOOL", style=Style(color=ThemeColors.TOOL_ACCENT, bold=True)
            )

            content = Text()
            content.append(self._current_status, style=Style(color=ThemeColors.FG))

            return Panel(
                content,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_ACCENT),
                padding=(0, 2),  # Reduced vertical padding
                expand=True,  # Expand to full width
            )

        elif self._status_type == "error":
            # Red theme for errors
            title = Text()
            title.append("✗ ", style=Style(color=ThemeColors.ERROR, bold=True))
            title.append("ERROR", style=Style(color=ThemeColors.ERROR, bold=True))

            content = Text()
            content.append(self._current_status, style=Style(color=ThemeColors.ERROR))

            return Panel(
                content,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.ERROR),
                padding=(0, 2),  # Reduced vertical padding
                expand=True,  # Expand to full width
            )

        elif self._status_type == "success":
            # Green theme for success
            title = Text()
            title.append("✓ ", style=Style(color=ThemeColors.SUCCESS, bold=True))
            title.append("SUCCESS", style=Style(color=ThemeColors.SUCCESS, bold=True))

            content = Text()
            content.append(self._current_status, style=Style(color=ThemeColors.FG))

            return Panel(
                content,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.SUCCESS),
                padding=(0, 2),  # Reduced vertical padding
                expand=True,  # Expand to full width
            )

        elif self._status_type == "summarizing":
            # Pink-orange theme for final response generation
            title = Text()
            title.append(
                spinner + " ", style=Style(color=ThemeColors.SUMMARY_ACCENT, bold=True)
            )
            title.append(
                "SUMMARIZING", style=Style(color=ThemeColors.SUMMARY_ACCENT, bold=True)
            )

            content = Text()
            content.append(self._current_status, style=Style(color=ThemeColors.FG))

            return Panel(
                content,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.SUMMARY_ACCENT),
                padding=(0, 2),  # Reduced vertical padding
                expand=True,  # Expand to full width
            )

        return Panel("")

    def _animate(self) -> None:
        """Animation loop for live display."""
        while self._active and not self._stop_event.is_set() and live:
            panel = self._get_status_panel()
            set_live_layer("status", panel)
            # Use shorter sleep to be responsive to stop event
            if self._stop_event.wait(timeout=0.1):
                break

    def _start_animation(self) -> None:
        """Start animation if not already running."""
        if not self._active:
            self._active = True
            self._stop_event.clear()

            start_live()

            # Stop any existing animation thread
            if self._animation_thread and self._animation_thread.is_alive():
                self._stop_event.set()
                # Wait a bit for thread to exit
                self._animation_thread.join(timeout=0.2)
                self._stop_event.clear()

            # Start animation in background thread
            self._animation_thread = threading.Thread(target=self._animate, daemon=True)
            self._animation_thread.start()

    def set_processing(self, message: str = "Processing your request...") -> None:
        """
        Set processing status with animated display.

        Args:
            message: Status message to display
        """
        self._current_status = message
        self._status_type = "processing"
        self._current_spinner = self._spinner_dots
        self._spinner_frame = 0  # Reset frame index when changing spinner

        self._start_animation()

    def set_executing(self, message: str = "Executing tool...") -> None:
        """
        Set executing status with animated display.

        Args:
            message: Status message to display
        """
        self._current_status = message
        self._status_type = "executing"
        self._current_spinner = self._spinner_arrows
        self._spinner_frame = 0  # Reset frame index when changing spinner

        self._start_animation()

    def set_summarizing(self, message: str = "Generating final response...") -> None:
        """
        Set summarizing status with animated display.

        Args:
            message: Status message to display
        """
        self._current_status = message
        self._status_type = "summarizing"
        self._current_spinner = self._spinner_stars
        self._spinner_frame = 0  # Reset frame index when changing spinner

        self._start_animation()

    def set_error(self, message: str = "Error occurred") -> None:
        """
        Set error status.

        Args:
            message: Error message to display
        """
        self._current_status = message
        self._status_type = "error"

        if self._active and live:
            set_live_layer("status", self._get_status_panel())

    def set_success(self, message: str = "Operation completed") -> None:
        """
        Set success status.

        Args:
            message: Success message to display
        """
        self._current_status = message
        self._status_type = "success"

        if self._active and live:
            set_live_layer("status", self._get_status_panel())
            time.sleep(0.5)  # Show success briefly

    def clear(self) -> None:
        """Clear the status display and stop animation thread."""
        if self._active:
            self._active = False

            # Signal animation thread to stop
            if self._stop_event:
                self._stop_event.set()

            # Wait for animation thread to exit
            if self._animation_thread and self._animation_thread.is_alive():
                self._animation_thread.join(timeout=0.5)

            # Stop Live display
            clear_live_layer("status")
            if not has_live_layers():
                stop_live()

            # Reset state
            self._current_status = None
            self._status_type = "idle"
            self._spinner_frame = 0

            # Clear stop event for next use
            self._stop_event.clear()

    def print_and_clear(self, content: str = "") -> None:
        """
        Print content and clear status display.

        Args:
            content: Content to print
        """
        self.clear()
        if content:
            console.print(content)

    def finish(self) -> None:
        """Finish current status and clear display."""
        self.clear()


# Global instance
_global_status: Optional[StatusManager] = None


def get_status_manager(console: Optional[Console] = None) -> StatusManager:
    """
    Get the global StatusManager instance.
    Returns:
        StatusManager instance
    """
    global _global_status
    if _global_status is None:
        _global_status = StatusManager()
    return _global_status
