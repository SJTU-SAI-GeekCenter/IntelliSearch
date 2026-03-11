"""
Loading Panel Component for Dynamic Status Display.

This module provides LoadingPanel for displaying animated loading states
with simple and intuitive API.

The LoadingPanel uses a standalone Live instance that starts/stops on demand,
avoiding conflicts with prompt_toolkit's input handling.
"""

import time
import threading
from typing import Optional, Any
from dataclasses import dataclass
from core.UI.theme import ThemeColors
from core.UI.console import console
from core.UI.live import live


@dataclass
class LoadingState:
    """Loading state configuration."""

    message: str
    mode: str  # processing, executing, summarizing, success, error
    spinner_type: str = "dots"
    title: Optional[str] = None


class LoadingPanel:
    """
    Dynamic loading panel with animated display.

    Provides simple API for managing loading states:
    - start_loading(): Start animated loading
    - end_loading(): Stop loading animation
    - success(): Show success state
    - fail(): Show error state
    - display(): Show static message

    Uses a standalone Live instance that starts/stops on demand,
    avoiding conflicts with prompt_toolkit.

    Example:
        >>> panel = LoadingPanel()
        >>> panel.start_loading("Processing data...")
        >>> # ... do work ...
        >>> panel.success("Data processed successfully!")
    """

    def __init__(self, console=None):
        """
        Initialize LoadingPanel.

        Args:
            console: Rich console instance (optional)
        """
        console = console
        self._active = False
        self._current_state: Optional[LoadingState] = None
        self._spinner_frame = 0
        self._animation_thread: Optional[threading.Thread] = None
        self._live: Optional[object] = None  # Standalone Live instance
        self._stop_event = threading.Event()  # Event to signal animation to stop

        # Spinner characters for different styles
        self._spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "stars": ["✶", "✷", "✸", "✹", "✺", "✴", "✳", "✲"],
        }

    def _get_spinner_char(self) -> str:
        """Get current spinner character."""
        if not self._current_state:
            return ""

        frames = self._spinners.get(
            self._current_state.spinner_type, self._spinners["dots"]
        )
        char = frames[self._spinner_frame]
        self._spinner_frame = (self._spinner_frame + 1) % len(frames)
        return char

    def _get_panel(self):
        """Get Rich Panel for current state."""
        if not self._current_state:
            return None

        try:
            from rich.panel import Panel
            from rich.text import Text
            from rich.style import Style
        except ImportError:
            return None

        # Color mapping for different modes
        color_map = {
            "processing": ThemeColors.ACCENT,
            "executing": ThemeColors.TOOL_ACCENT,
            "summarizing": ThemeColors.SUMMARY_ACCENT,
            "success": ThemeColors.SUCCESS,
            "error": ThemeColors.ERROR,
            "fail": ThemeColors.ERROR,
        }

        color = color_map.get(self._current_state.mode, ThemeColors.PRIMARY)

        # Build title
        title = Text()

        if self._current_state.mode == "success":
            title.append("✓ ", style=Style(color=ThemeColors.SUCCESS, bold=True))
            title.append("SUCCESS", style=Style(color=ThemeColors.SUCCESS, bold=True))
        elif self._current_state.mode in ["error", "fail"]:
            title.append("✗ ", style=Style(color=ThemeColors.ERROR, bold=True))
            title.append("ERROR", style=Style(color=ThemeColors.ERROR, bold=True))
        else:
            # Show spinner for loading states
            spinner = self._get_spinner_char()
            title.append(spinner + " ", style=Style(color=color, bold=True))
            title.append(
                self._current_state.mode.upper(), style=Style(color=color, bold=True)
            )

        # Override with custom title if provided
        if self._current_state.title:
            title = Text()
            title.append(self._current_state.title, style=Style(color=color, bold=True))

        # Build content
        content = Text()
        content.append(self._current_state.message, style=Style(color=ThemeColors.FG))

        # Create panel (Panel takes content as first positional arg)
        return Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=color),
            padding=(0, 2),
        )

    def _animate_loop(self):
        """Animation loop for live display."""
        while self._active and not self._stop_event.is_set():
            panel = self._get_panel()
            if panel and self._live:
                try:
                    self._live.update(panel)
                except Exception:
                    pass
            time.sleep(0.1)  # 100ms per frame

    def start_loading(
        self, message: str, mode: str = "processing", spinner_type: str = "dots"
    ):
        """
        Start animated loading display.

        Args:
            message: Loading message to display
            mode: Loading mode (processing, executing, summarizing)
            spinner_type: Animation style (dots, arrows, stars)

        Example:
            >>> panel = LoadingPanel()
            >>> panel.start_loading("Processing data...", mode="processing")
        """
        try:
            from rich.live import Live
        except ImportError:
            print(f"[{mode.upper()}] {message}")
            return

        # Stop any existing loading
        if self._active:
            self.end_loading()

        # Set current state
        self._current_state = LoadingState(
            message=message, mode=mode, spinner_type=spinner_type
        )
        self._active = True
        self._stop_event.clear()

        # Create and start Live instance
        panel = self._get_panel()
        if panel:
            self._live = live
            self._live.start()
            time.sleep(2)
            # Start animation thread
            self._animation_thread = threading.Thread(
                target=self._animate_loop, daemon=True
            )
            self._animation_thread.start()

    def end_loading(self):
        """
        Stop loading animation and clear display.

        Example:
            >>> panel.start_loading("Loading...")
            >>> # ... do work ...
            >>> panel.end_loading()
        """
        if not self._active:
            return

        self._active = False
        self._stop_event.set()

        # Stop Live instance
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

        # Wait for animation thread to finish
        if self._animation_thread:
            self._animation_thread.join(timeout=0.5)
            self._animation_thread = None

        self._current_state = None
        self._spinner_frame = 0

    def update(self, message: str):
        """
        Update loading message without stopping animation.

        Args:
            message: New message to display

        Example:
            >>> panel.start_loading("Initializing...")
            >>> panel.update("Loading data...")
            >>> panel.update("Processing data...")
            >>> panel.end_loading()
        """
        if self._current_state:
            self._current_state.message = message

    def success(self, message: str, auto_clear: bool = True, delay: float = 0.5):
        """
        Show success state.

        Args:
            message: Success message
            auto_clear: Whether to auto-clear after delay
            delay: Delay in seconds before auto-clearing

        Example:
            >>> panel.start_loading("Processing...")
            >>> # ... do work ...
            >>> panel.success("Processing completed!")
        """
        # Stop any loading animation
        if self._active:
            self.end_loading()

        # Update state to success
        self._current_state = LoadingState(message=message, mode="success")

        # Display success panel
        panel = self._get_panel()
        if panel:
            try:
                from rich.live import Live

                self._live = live
                self._live.start()
            except Exception:
                if console:
                    console.print(panel)

        # Auto-clear if requested
        if auto_clear:
            time.sleep(delay)
            self.end_loading()

    def fail(self, message: str, auto_clear: bool = True, delay: float = 2.0):
        """
        Show error/failure state.

        Args:
            message: Error message
            auto_clear: Whether to auto-clear after delay
            delay: Delay in seconds before auto-clearing

        Example:
            >>> panel.start_loading("Processing...")
            >>> # ... error occurs ...
            >>> panel.fail("Processing failed: timeout")
        """
        # Stop any loading animation
        if self._active:
            self.end_loading()

        # Update state to error
        self._current_state = LoadingState(message=message, mode="error")

        # Display error panel
        panel = self._get_panel()
        if panel:
            try:
                from rich.live import Live

                self._live = live
                self._live.start()
            except Exception:
                if console:
                    console.print(panel)

        # Auto-clear if requested
        if auto_clear:
            time.sleep(delay)
            self.end_loading()

    def display(self, message: str, title: Optional[str] = None, style: str = "normal"):
        """
        Display a static message (non-animated).

        Stops any active loading animation before displaying.

        Args:
            message: Message to display
            title: Optional title
            style: Style (normal, success, warning, error, info)

        Example:
            >>> panel.display("Hello, World!", title="Notice")
        """
        # Stop any active loading
        if self._active:
            self.end_loading()

        try:
            from rich.panel import Panel
            from rich.text import Text
            from rich.style import Style
        except ImportError:
            if title:
                print(f"[{title}] {message}")
            else:
                print(message)
            return

        # Color mapping
        color_map = {
            "normal": ThemeColors.FG,
            "success": ThemeColors.SUCCESS,
            "warning": ThemeColors.WARNING,
            "error": ThemeColors.ERROR,
            "info": ThemeColors.INFO,
        }
        color = color_map.get(style, ThemeColors.FG)

        # Build content
        content = Text()
        content.append(message, style=Style(color=color))

        # Create panel (Panel takes content as first positional arg)
        if title:
            panel = Panel(
                content,
                title=title,
                border_style=Style(color=color),
                padding=(0, 1),
            )
        else:
            panel = Panel(
                content,
                border_style=Style(color=color),
                padding=(0, 1),
            )

        # Print to console
        if console:
            console.print(panel)
        else:
            from rich.console import Console

            Console().print(panel)

    def clear(self):
        """
        Clear the display and stop any animations.

        Example:
            >>> panel.start_loading("Loading...")
            >>> panel.clear()
        """
        self.end_loading()


# ============ 工厂函数 ============


def create_loading_panel(console=None) -> LoadingPanel:
    """
    创建 LoadingPanel 实例的工厂函数。

    Args:
        console: Rich console instance (optional)

    Returns:
        LoadingPanel 实例

    Examples:
        >>> # 方式1：使用工厂函数
        >>> panel = create_loading_panel()
        >>> panel.start_loading("Loading...")
        >>>
        >>> # 方式2：直接创建实例
        >>> from core.UI.components.loading import LoadingPanel
        >>> panel = LoadingPanel()
        >>> panel.start_loading("Loading...")
    """
    return LoadingPanel(console=console)
