"""
Select control for option selection.

This module provides the SelectControl for single and
multiple option selection from a list.
"""

import sys
import os
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from .base_component import BaseUIComponent
from core.UI.theme import ThemeColors

if TYPE_CHECKING:
    from core.UI.cli_renderer import CLIRenderer


@dataclass
class SelectResult:
    """Result of select operation"""

    success: bool
    selected_indices: Optional[List[int]] = None
    selected_options: Optional[List[str]] = None
    error: Optional[str] = None


@dataclass
class SelectControl:
    """
    Option selection control.

    Attributes:
        message: Prompt message
        options: List of options to choose from
        default_index: Default selected index (for single select)
        allow_multiple: Whether multiple selection is allowed
        default_indices: Default selected indices (for multiple select)
        cancel_allowed: Whether user can cancel
    """

    message: str
    options: List[str]
    default_index: int = 0
    allow_multiple: bool = False
    default_indices: Optional[List[int]] = None
    cancel_allowed: bool = True

    def __post_init__(self):
        """Validate select parameters."""
        if not self.options:
            raise ValueError("options list cannot be empty")

        n_options = len(self.options)

        # Validate default_index
        if self.default_index < 0 or self.default_index >= n_options:
            self.default_index = 0

        # Validate default_indices
        if self.default_indices is not None:
            for idx in self.default_indices:
                if idx < 0 or idx >= n_options:
                    raise ValueError(f"Invalid default index: {idx}")

        # Ensure consistency
        if self.allow_multiple:
            if self.default_indices is None:
                self.default_indices = [self.default_index]
        else:
            if self.default_indices is not None and len(self.default_indices) > 1:
                # For single select, only use the first index
                self.default_index = self.default_indices[0]
                self.default_indices = None

    def validate_index(self, index: int) -> tuple[bool, Optional[str]]:
        """
        Validate a single selection index.

        Args:
            index: The index to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not (0 <= index < len(self.options)):
            return False, f"Invalid selection: {index}"
        return True, None

    def validate_indices(self, indices: List[int]) -> tuple[bool, Optional[str]]:
        """
        Validate multiple selection indices.

        Args:
            indices: The indices to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for idx in indices:
            valid, error = self.validate_index(idx)
            if not valid:
                return False, error
        return True, None

    def get_selected_option(self, index: int) -> str:
        """
        Get the option at the given index.

        Args:
            index: The index of the option

        Returns:
            The option string
        """
        if not (0 <= index < len(self.options)):
            raise IndexError(f"Invalid index: {index}")
        return self.options[index]

    def __rich__(self):
        """
        Render as a Rich renderable.

        Returns:
            Rich Panel showing options list
        """
        content = Text()

        # Add message
        content.append(self.message, style=Style(color=ThemeColors.PRIMARY, bold=True))
        content.append("\n\n")

        # Add options with indices
        for i, option in enumerate(self.options):
            # Mark default option
            prefix = ""
            if not self.allow_multiple and i == self.default_index:
                prefix = "★ "
            elif (
                self.allow_multiple
                and self.default_indices
                and i in self.default_indices
            ):
                prefix = "✓ "
            else:
                prefix = "  "

            # Format option line
            option_text = f"{prefix}[{i}] {option}"
            content.append(option_text)
            content.append("\n")

        # Add hint
        content.append("\n")
        hint = "提示：输入选项编号"
        if self.allow_multiple:
            hint += "（支持多选）"
        if self.cancel_allowed:
            hint += "，Ctrl+C取消"
        content.append(hint, style=Style(dim=True))

        return Panel(
            content,
            title="📋 选择",
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(0, 1),
        )


class TUISelectControl:
    """TUI select control based on Rich Live (transient=True)"""

    def __init__(
        self,
        options: List[str],
        default_index: int = 0,
        allow_multiple: bool = False,
        default_indices: Optional[List[int]] = None,
    ):
        self.options = options
        self.curr_idx = default_index
        self.allow_multiple = allow_multiple
        self.selected_indices = set(default_indices) if default_indices else set()
        self._confirmed = False

    def render(self):
        """Render select control"""
        lines = []
        for i, opt in enumerate(self.options):
            if self.allow_multiple:
                prefix = "✓" if i in self.selected_indices else " "
                if i == self.curr_idx:
                    lines.append(
                        f"[bold reverse green] > [{prefix}] {opt} [/bold reverse green]"
                    )
                else:
                    lines.append(f"   [{prefix}] {opt}")
            else:
                if i == self.curr_idx:
                    lines.append(f"[bold reverse green] > {opt} [/bold reverse green]")
                else:
                    lines.append(f"   {opt}")

        lines.append("")
        if self.allow_multiple:
            selected_text = ", ".join(
                [self.options[i] for i in sorted(self.selected_indices)]
            )
            lines.append(f"[dim]已选择: {selected_text}")
            lines.append(
                "[dim yellow]空格键: 切换选择  Enter: 完成  ↑↓: 移动[/dim yellow]"
            )
        else:
            lines.append("[dim yellow]提示：使用↑↓键选择，Enter确认[/dim yellow]")

        return "\n".join(lines)

    def handle_key(self, key: str) -> bool:
        """Handle key input, return True if confirmed"""
        if key == "up":
            self.curr_idx = (self.curr_idx - 1) % len(self.options)
        elif key == "down":
            self.curr_idx = (self.curr_idx + 1) % len(self.options)
        elif key == "enter":
            self._confirmed = True
            return True
        elif key == " " and self.allow_multiple:
            if self.curr_idx in self.selected_indices:
                self.selected_indices.remove(self.curr_idx)
            else:
                self.selected_indices.add(self.curr_idx)
        return False


class SelectComponent(BaseUIComponent):
    """Select component for user selection."""

    def render_cli(
        self, data: SelectControl, renderer: "CLIRenderer", mode="cli", **kwargs
    ) -> SelectResult:
        """
        Handle user selection for CLI.

        Args:
            data: SelectControl instance
            renderer: CLI renderer instance
            mode: "cli" or "tui"
            **kwargs: Additional parameters

        Returns:
            SelectResult with selected option
        """
        if mode == "tui" and renderer.is_available() and sys.stdin.isatty():
            return self._render_tui(data, renderer)

        return self._render_cli(data, renderer)

    def _render_cli(self, data: SelectControl, renderer: "CLIRenderer") -> SelectResult:
        """Render in CLI mode."""
        if not renderer.is_available():
            print(f"{data.message}")
            for i, option in enumerate(data.options):
                print(f"  [{i}] {option}")
            try:
                idx = int(input("> "))
                return SelectResult(
                    success=True,
                    selected_indices=[idx],
                    selected_options=[data.options[idx]],
                )
            except (ValueError, IndexError):
                return SelectResult(
                    success=True,
                    selected_indices=[data.default_index],
                    selected_options=[data.options[data.default_index]],
                )

        selected = renderer.Prompt.ask(
            data.message,
            choices=data.options,
            default=data.options[data.default_index],
        )
        return SelectResult(
            success=True,
            selected_indices=[data.options.index(selected)],
            selected_options=[selected],
        )

    def _render_tui(self, data: SelectControl, renderer: "CLIRenderer") -> SelectResult:
        """Render in TUI mode."""
        tui_select = TUISelectControl(
            options=data.options,
            default_index=data.default_index,
            allow_multiple=data.allow_multiple,
            default_indices=data.default_indices,
        )

        console = renderer.Console()

        console.print(f"[bold]{data.message}[/bold]")
        if tui_select.allow_multiple:
            console.print(
                "[dim yellow]提示：使用↑↓键选择，Enter确认，已选中的选项会高亮显示"
            )
        else:
            console.print("[dim yellow]提示：使用↑↓键选择，Enter确认")
        console.print()

        with renderer.Live(
            tui_select.render(), transient=True, auto_refresh=False
        ) as live:
            try:
                while not tui_select._confirmed:
                    key = self._get_key()
                    if key is None:
                        continue

                    if tui_select.handle_key(key):
                        if tui_select._confirmed:
                            break
                        else:
                            live.update(tui_select.render(), refresh=True)
                    else:
                        live.update(tui_select.render(), refresh=True)

            except KeyboardInterrupt:
                if data.cancel_allowed:
                    return SelectResult(success=False, error="Interrupted by user")

        if tui_select.allow_multiple:
            selected_indices = sorted(tui_select.selected_indices)
            selected_options = [tui_select.options[i] for i in selected_indices]
        else:
            selected_indices = [tui_select.curr_idx]
            selected_options = [tui_select.options[tui_select.curr_idx]]

        return SelectResult(
            success=True,
            selected_indices=selected_indices,
            selected_options=selected_options,
        )

    def _get_key(self) -> Optional[str]:
        """Cross-platform key reading."""
        if os.name == "nt":
            import msvcrt

            key = msvcrt.getch()
            if key in [b"\x00", b"\xe0"]:
                key = msvcrt.getch()
                return {"H": "up", "P": "down"}.get(key.decode(), None)
            elif key == b" ":
                return " "
            elif key in [b"\r", b"\n"]:
                return "enter"
            return None
        else:
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    ch += sys.stdin.read(2)
                    return {"\x1b[A": "up", "\x1b[B": "down"}.get(ch, None)
                elif ch == " ":
                    return " "
                elif ch in ("\r", "\n"):
                    return "enter"
                return None

            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ============ 工厂函数 ============


def create_select(**kwargs) -> SelectControl:
    """
    创建 SelectControl 对象的工厂函数。

    支持两种调用方式：
    1. 直接传递参数：create_select(message="请选择", options=["选项1", "选项2"])
    2. 传递字典/JSON：create_select(**{"message": "请选择", "options": ["选项1", "选项2"]})

    Args:
        message: 提示消息
        options: 选项列表
        default_index: 默认选中的索引（单选）
        allow_multiple: 是否允许多选
        default_indices: 默认选中的索引列表（多选）
        cancel_allowed: 是否允许取消

    Returns:
        SelectControl 对象

    Examples:
        >>> # 方式1：直接传递参数
        >>> select = create_select(message="请选择颜色", options=["红色", "蓝色", "绿色"])
        >>>
        >>> # 方式2：传递字典
        >>> config = {"message": "请选择", "options": ["A", "B", "C"], "allow_multiple": True}
        >>> select = create_select(**config)
    """
    return SelectControl(**kwargs)
