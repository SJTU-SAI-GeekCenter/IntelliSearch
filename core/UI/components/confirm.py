"""
Confirm control for confirmation dialogs.

This module provides the ConfirmControl for user
confirmation of actions or decisions.
"""

import sys
import os
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from .base_component import BaseUIComponent
from core.UI.theme import ThemeColors

if TYPE_CHECKING:
    from core.UI.cli_renderer import CLIRenderer


@dataclass
class ConfirmResult:
    """Result of confirm operation"""

    success: bool
    confirmed: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class ConfirmControl:
    """
    Confirmation dialog control.

    Attributes:
        message: Confirmation message
        title: Dialog title
        default_choice: Default choice (True=confirm, False=cancel)
        cancel_allowed: Whether user can cancel
    """

    message: str
    title: str = "确认操作"
    default_choice: bool = False
    cancel_allowed: bool = True

    def get_prompt_text(self) -> str:
        """
        Get the prompt text for CLI display.

        Returns:
            Formatted prompt string
        """
        prompt = f"{self.message} ("
        if self.cancel_allowed:
            prompt += "y/n/c"  # yes/no/cancel
        else:
            prompt += "y/n"  # yes/no only

        if self.default_choice:
            prompt += " [Y]"
        else:
            prompt += " [N]"

        prompt += ")"
        return prompt

    def __rich__(self):
        """
        Render as a Rich renderable.

        Returns:
            Rich Panel showing confirmation dialog
        """
        content = Text()

        # Add title
        content.append(
            f"{self.title}:", style=Style(color=ThemeColors.PRIMARY, bold=True)
        )
        content.append("\n")

        # Add message
        content.append(self.message, style=Style(color=ThemeColors.FG))
        content.append("\n\n")

        # Add prompt hint
        hint = "提示："
        if self.default_choice:
            hint += " [Y] 是 [N] 否"
        else:
            hint += " [Y] 是 [N] 否"
        if self.cancel_allowed:
            hint += " [C] 取消"
        content.append(hint, style=Style(dim=True))

        return Panel(
            content,
            title="❓ 确认",
            border_style=Style(color=ThemeColors.WARNING),
            padding=(0, 1),
        )


class ConfirmComponent(BaseUIComponent):
    """Confirm component for user confirmation."""

    def render_cli(
        self, data: ConfirmControl, renderer: "CLIRenderer", mode="cli", **kwargs
    ) -> ConfirmResult:
        """
        Handle user confirmation for CLI.

        Args:
            data: ConfirmControl instance
            renderer: CLI renderer instance
            mode: "cli" or "tui"
            **kwargs: Additional parameters

        Returns:
            ConfirmResult with user's choice
        """
        if mode == "tui" and renderer.is_available() and sys.stdin.isatty():
            return self._render_tui(data, renderer)

        return self._render_cli(data, renderer)

    def _render_cli(
        self, data: ConfirmControl, renderer: "CLIRenderer"
    ) -> ConfirmResult:
        """Render in CLI mode."""
        if not renderer.is_available():
            print(f"{data.title}")
            print(f"{data.message}")
            print(f"(Default: {'Yes' if data.default_choice else 'No'})")
            response = input("[y/N] > ").lower()
            if response in ["y", "yes"]:
                return ConfirmResult(success=True, confirmed=True)
            elif response in ["n", "no"]:
                return ConfirmResult(success=True, confirmed=False)
            return ConfirmResult(success=True, confirmed=data.default_choice)

        confirmed = renderer.Confirm.ask(
            data.message,
            default=data.default_choice,
        )
        return ConfirmResult(success=True, confirmed=confirmed)

    def _render_tui(
        self, data: ConfirmControl, renderer: "CLIRenderer"
    ) -> ConfirmResult:
        """Render in TUI mode."""
        console = renderer.Console()

        console.print(f"[bold]1. {data.title}:[/bold]")
        console.print(f"[dim]{data.message}[/dim]")
        console.print()

        confirm_options = ["取消", "确认"]
        if data.default_choice:
            curr_idx = 1
        else:
            curr_idx = 0

        def make_confirm_menu():
            lines = []
            for i, opt in enumerate(confirm_options):
                if i == curr_idx:
                    # 只高亮当前选中的项
                    if i == 1:  # 确认
                        lines.append("[bold reverse green] > 确认[/bold reverse green]")
                    else:  # 取消
                        lines.append(
                            "[bold reverse yellow] > 取消[/bold reverse yellow]"
                        )
                else:
                    # 未选中的项正常显示
                    lines.append(f"   {opt}")
            return "\n".join(lines)

        with renderer.Live(
            make_confirm_menu(), transient=True, auto_refresh=False
        ) as live:
            try:
                while True:
                    key = self._get_key()
                    if key is None:
                        continue

                    if key == "up":
                        curr_idx = (curr_idx - 1) % len(confirm_options)
                    elif key == "down":
                        curr_idx = (curr_idx + 1) % len(confirm_options)
                    elif key == "enter":
                        break

                    live.update(make_confirm_menu(), refresh=True)

            except KeyboardInterrupt:
                if data.cancel_allowed:
                    return ConfirmResult(success=False, error="Interrupted by user")

        confirmed = curr_idx == 1
        console.print()
        if confirmed:
            console.print("[bold green]✅ 确认操作[/bold green]\n")
        else:
            console.print("[bold yellow]❌ 取消操作[/bold yellow]\n")

        return ConfirmResult(success=True, confirmed=confirmed)

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


def create_confirm(**kwargs) -> ConfirmControl:
    """
    创建 ConfirmControl 对象的工厂函数。

    支持两种调用方式：
    1. 直接传递参数：create_confirm(message="确定要删除吗？")
    2. 传递字典/JSON：create_confirm(**{"message": "确定要删除吗？", "default_choice": False})

    Args:
        message: 确认消息
        title: 对话框标题
        default_choice: 默认选择（True=确认，False=取消）
        cancel_allowed: 是否允许取消

    Returns:
        ConfirmControl 对象

    Examples:
        >>> # 方式1：直接传递参数
        >>> confirm = create_confirm(message="确定要删除文件吗？")
        >>>
        >>> # 方式2：传递字典
        >>> config = {"message": "确定要继续吗？", "title": "危险操作确认"}
        >>> confirm = create_confirm(**config)
    """
    return ConfirmControl(**kwargs)
