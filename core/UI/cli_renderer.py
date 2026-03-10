"""
CLI renderer for UI components.

This module handles rendering of UI components to the command line interface
using Rich library for enhanced terminal display.
Supports both CLI and TUI modes for user interactions.

This is a lightweight renderer that delegates to individual components.
"""

import os
from typing import Optional
from core.UI.base_renderer import BaseRenderer
from core.UI.theme import ThemeColors
from core.UI.console import console
from core.UI.live import live


class CLIRenderer(BaseRenderer):
    """
    Renders UI components to the CLI using Rich library.
    Supports both CLI and TUI interaction modes.

    This is a lightweight renderer that provides basic display methods
    and delegates complex rendering to individual components.
    """

    def __init__(self):
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text
            from rich.prompt import Prompt, Confirm
            from rich.live import Live
            from rich.box import DOUBLE

            self.Console = Console
            self.Panel = Panel
            self.Text = Text
            self.Prompt = Prompt
            self.Confirm = Confirm
            self.Live = Live
            self.DOUBLE_BOX = DOUBLE
            self._available = True
        except ImportError:
            self._available = False
            print("Warning: Rich library not found. Falling back to basic rendering.")

    def is_available(self) -> bool:
        """Check if Rich library is available"""
        return self._available

    def prompt_input(self, control) -> str:
        """
        Prompt user for text input using InputComponent.

        Args:
            control: Input control with message, placeholder, etc.

        Returns:
            User input string
        """
        from core.UI.components import InputComponent

        component = InputComponent()
        return component.render_cli(control, self)

    def prompt_select(self, control) -> str:
        """
        Prompt user to select an option using SelectComponent.

        自动检测环境并选择最佳模式：
        - 在交互式终端中使用TUI模式（带箭头键导航的交互式菜单）
        - 在非交互式环境或测试中使用CLI模式

        Args:
            control: Select control with options and default

        Returns:
            Selected option string
        """
        from core.UI.components import SelectComponent

        component = SelectComponent()
        # 使用TUI模式（如果可用），否则降级到CLI模式
        result = component.render_cli(control, self, mode="tui")
        if result.success and result.selected_options:
            return result.selected_options[0]
        return control.options[control.default_index]

    def prompt_confirm(self, control) -> bool:
        """
        Prompt user for confirmation using ConfirmComponent.

        自动检测环境并选择最佳模式：
        - 在交互式终端中使用TUI模式（带箭头键导航的交互式菜单）
        - 在非交互式环境或测试中使用CLI模式

        Args:
            control: Confirm control with message and title

        Returns:
            True if confirmed, False otherwise
        """
        from core.UI.components import ConfirmComponent

        component = ConfirmComponent()
        # 使用TUI模式（如果可用），否则降级到CLI模式
        result = component.render_cli(control, self, mode="tui")
        if result.success and result.confirmed is not None:
            return result.confirmed
        return control.default_choice

    def _render_text_with_formatting(self, text_parts) -> "self.Text":
        """
        Render text parts with Rich formatting support.

        Args:
            text_parts: Iterable of text strings that may contain Rich formatting tags

        Returns:
            Rich Text object with formatted content
        """
        if not self._available:
            return "".join(str(part) for part in text_parts)

        full_text = " ".join(str(part) for part in text_parts)
        Text_class = self.Text
        return Text_class.from_markup(full_text)

    def display(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a message with default styling using DisplayControl.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[{title}]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="normal",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()

    def display_fatal(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a fatal error message with deep red styling and double border.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[FATAL] {title}")
            else:
                print(f"[FATAL]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="fatal",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()

    def display_critical(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a critical error message with red styling.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[CRITICAL] {title}")
            else:
                print(f"[CRITICAL]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="critical",
            title=title,
        )
        live.console.print(display_control)

    def display_notice(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a notice message with blue styling.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[NOTICE] {title}")
            else:
                print(f"[NOTICE]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="notice",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()

    def display_success(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a success message with green styling.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[SUCCESS] {title}")
            else:
                print(f"[SUCCESS]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="success",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()

    def display_warning(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display a warning message with yellow styling.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[WARNING] {title}")
            else:
                print(f"[WARNING]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="warning",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()

    def display_error(self, *args, title: Optional[str] = None, **kwargs):
        """
        Display an error message with red styling.

        Args:
            *args: Text parts to display (supports Rich formatting)
            title: Optional title for the message box
            **kwargs: Additional parameters
        """
        if not self._available:
            message = " ".join(str(arg) for arg in args)
            if title:
                print(f"[ERROR] {title}")
            else:
                print(f"[ERROR]")
            print(message)
            return

        from core.UI.components import DisplayControl

        # Create DisplayControl and use its __rich__ method
        display_control = DisplayControl(
            text=" ".join(str(arg) for arg in args),
            style="error",
            title=title,
        )
        self.Console().print(display_control)
        self.Console().print()
