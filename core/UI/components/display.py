"""
Display control for non-interactive text display.

This module provides the DisplayControl for showing
static text content in various styles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED, DOUBLE, SQUARE, HEAVY, ASCII
from .base_component import BaseUIComponent
from core.UI.console import console
from core.UI.theme import ThemeColors

if TYPE_CHECKING:
    from core.UI.cli_renderer import CLIRenderer


class DisplayStyle(str, Enum):
    """Display style options."""

    NORMAL = "normal"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    FATAL = "fatal"
    CRITICAL = "critical"
    NOTICE = "notice"


@dataclass
class DisplayControl:
    """
    Non-interactive text display control.

    Attributes:
        text: The text to display
        style: Display style (normal, success, warning, error, info, fatal, critical, notice)
        markdown: Whether to parse markdown (if supported)
        show_border: Whether to show border (default True)
        border_color: Custom border color (hex code or color name)
        text_color: Custom text color (hex code or color name)
        border_style: Custom border style (Rich panel style)
        title: Custom title (overrides default)
    """

    text: str
    style: str = "normal"
    markdown: bool = False
    show_border: bool = True
    border_color: Optional[str] = None
    text_color: Optional[str] = None
    border_style: Optional[str] = None
    title: Optional[str] = None

    def __post_init__(self):
        """Validate style is a valid DisplayStyle."""
        if isinstance(self.style, str):
            try:
                self.style = DisplayStyle(self.style).value
            except ValueError:
                self.style = DisplayStyle.NORMAL.value

    def __rich__(self):
        """
        Render as a Rich renderable with consistent styling matching CLIRenderer.

        Returns:
            Rich Panel with styled content
        """
        from rich.box import DOUBLE

        # Map style to colors and icons (matching CLIRenderer)
        style_config = {
            "normal": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.PRIMARY,
                "icon": None,
                "title": None,
                "box": None,
            },
            "success": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.SUCCESS,
                "icon": "✓ ",
                "title": "Success",
                "box": None,
            },
            "warning": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.WARNING,
                "icon": "⚠ ",
                "title": " Warning",
                "box": None,
            },
            "error": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.ERROR,
                "icon": "✗ ",
                "title": "Error",
                "box": None,
            },
            "info": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.INFO,
                "icon": None,
                "title": None,
                "box": None,
            },
            "fatal": {
                "fg_color": ThemeColors.FATAL,
                "border_color": ThemeColors.FATAL,
                "icon": "💀 ",
                "title": "FATAL",
                "box": DOUBLE,
            },
            "critical": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.CRITICAL,
                "icon": "❌ ",
                "title": "CRITICAL",
                "box": None,
            },
            "notice": {
                "fg_color": ThemeColors.FG,
                "border_color": ThemeColors.NOTICE,
                "icon": "ℹ️ ",
                "title": " Notice",
                "box": None,
            },
        }

        config = style_config.get(self.style, style_config["normal"])

        # Apply custom colors if provided
        fg_color = self.text_color if self.text_color else config["fg_color"]
        border_color = (
            self.border_color if self.border_color else config["border_color"]
        )

        # Handle no-border mode
        if not self.show_border:
            return Text(self.text, style=Style(color=fg_color))

        # Create content (support Rich formatting)
        content = Text.from_markup(self.text)
        content.style = Style(color=fg_color)

        # Create title (with icon if configured)
        title = None
        if self.title:
            title = Text(self.title, style=Style(color=border_color, bold=True))
        elif config["icon"]:
            title = Text()
            title.append(config["icon"], style=Style(color=border_color))
            title.append(config["title"], style=Style(color=border_color, bold=True))

        panel_kwargs = {
            "border_style": Style(color=border_color),
            "padding": (0, 1),
            "expand": True,
            "title_align": "left",
        }

        # Apply custom border style if provided
        box_map = {
            "rounded": ROUNDED,
            "double": DOUBLE,
            "square": SQUARE,
            "heavy": HEAVY,
            "ascii": ASCII,
        }
        if self.border_style:
            if isinstance(self.border_style, str):
                panel_kwargs["box"] = box_map.get(self.border_style.lower(), ROUNDED)
            else:
                panel_kwargs["box"] = self.border_style
        elif config["box"]:
            panel_kwargs["box"] = config["box"]

        return Panel(content, title=title, **panel_kwargs)


class DisplayComponent(BaseUIComponent):
    """Component for rendering DisplayControl to CLI."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """
        Render display control in CLI mode.

        Args:
            data: DisplayControl instance
            renderer: CLI renderer instance
            **kwargs: Additional parameters

        Returns:
            Rendered content
        """
        if not renderer.is_available():
            print(data.text)
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        # Map style to colors
        style_map = {
            "normal": (ThemeColors.FG, ThemeColors.PRIMARY),
            "success": (ThemeColors.FG, ThemeColors.SUCCESS),
            "warning": (ThemeColors.FG, ThemeColors.WARNING),
            "error": (ThemeColors.FG, ThemeColors.ERROR),
            "info": (ThemeColors.FG, ThemeColors.INFO),
            "fatal": (ThemeColors.FG, ThemeColors.FATAL),
            "critical": (ThemeColors.FG, ThemeColors.CRITICAL),
            "notice": (ThemeColors.FG, ThemeColors.NOTICE),
        }

        fg_color, border_color = style_map.get(data.style, style_map["normal"])

        # Apply custom colors if provided
        if data.text_color:
            fg_color = data.text_color
        if data.border_color:
            border_color = data.border_color

        # Handle no-border mode
        if not data.show_border:
            renderer.Console().print(Text(data.text, style=Style(color=fg_color)))
            renderer.Console().print()
            return None

        content = Text()
        content.append(data.text, style=Style(color=fg_color))

        panel_kwargs = {
            "border_style": Style(color=border_color),
            "padding": (0, 1),
        }

        # Apply custom border style if provided
        if data.border_style:
            panel_kwargs["box"] = data.border_style

        panel = Panel(content, **panel_kwargs)

        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


class DisplaySuccessComponent(BaseUIComponent):
    """Component for rendering success messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render success message in CLI mode."""
        if not renderer.is_available():
            print(f"[SUCCESS] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("✓ ", style=Style(color=ThemeColors.SUCCESS))
        title.append("Success", style=Style(color=ThemeColors.SUCCESS, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FG))

        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=ThemeColors.SUCCESS),
            padding=(0, 1),
        )

        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


class DisplayWarningComponent(BaseUIComponent):
    """Component for rendering warning messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render warning message in CLI mode."""
        if not renderer.is_available():
            print(f"[WARNING] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("⚠ ", style=Style(color=ThemeColors.WARNING))
        title.append("Warning", style=Style(color=ThemeColors.WARNING, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FG))

        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=ThemeColors.WARNING),
            padding=(0, 1),
        )

        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


class DisplayErrorComponent(BaseUIComponent):
    """Component for rendering error messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render error message in CLI mode."""
        if not renderer.is_available():
            print(f"[ERROR] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("✗ ", style=Style(color=ThemeColors.ERROR))
        title.append("Error", style=Style(color=ThemeColors.ERROR, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FG))

        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=ThemeColors.ERROR),
            padding=(0, 1),
        )

        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


class DisplayFatalComponent(BaseUIComponent):
    """Component for rendering fatal error messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render fatal error message in CLI mode."""
        if not renderer.is_available():
            print(f"[FATAL] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("💀 ", style=Style(color=ThemeColors.FATAL))
        title.append("FATAL", style=Style(color=ThemeColors.FATAL, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FATAL, bold=True))

        panel_kwargs = {
            "content": content,
            "title": title,
            "title_align": "left",
            "border_style": Style(color=ThemeColors.FATAL),
            "padding": (0, 1),
        }

        # Use thicker border for fatal errors
        if data.border_style is None:
            panel_kwargs["box"] = "double"

        panel = Panel(**panel_kwargs)
        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


class DisplayCriticalComponent(BaseUIComponent):
    """Component for rendering critical error messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render critical error message in CLI mode."""
        if not renderer.is_available():
            print(f"[CRITICAL] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("❌ ", style=Style(color=ThemeColors.CRITICAL))
        title.append("CRITICAL", style=Style(color=ThemeColors.CRITICAL, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FG))

        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=ThemeColors.CRITICAL),
            padding=(0, 1),
        )
        # renderer.Console().print(panel)
        console.print(panel)

        return panel


class DisplayNoticeComponent(BaseUIComponent):
    """Component for rendering notice messages."""

    def render_cli(self, data: DisplayControl, renderer: "CLIRenderer", **kwargs):
        """Render notice message in CLI mode."""
        if not renderer.is_available():
            print(f"[NOTICE] {data.text}")
            return None

        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style
        from core.UI.theme import ThemeColors

        title = Text()
        title.append("ℹ️ ", style=Style(color=ThemeColors.NOTICE))
        title.append("Notice", style=Style(color=ThemeColors.NOTICE, bold=True))

        content = Text()
        content.append(data.text, style=Style(color=ThemeColors.FG))

        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=Style(color=ThemeColors.NOTICE),
            padding=(0, 1),
        )

        renderer.Console().print(panel)
        renderer.Console().print()

        return panel


# ============ 工厂函数 ============


def create_display(**kwargs) -> DisplayControl:
    """
    创建 DisplayControl 对象的工厂函数。

    支持两种调用方式：
    1. 直接传递参数：create_display(text="消息", style="error")
    2. 传递字典/JSON：create_display(**{"text": "消息", "style": "error"})

    Args:
        text: 要显示的文本
        style: 显示样式 (normal, success, warning, error, info, fatal, critical, notice)
        markdown: 是否解析 markdown
        show_border: 是否显示边框
        border_color: 自定义边框颜色
        text_color: 自定义文本颜色
        border_style: 自定义边框样式
        title: 自定义标题

    Returns:
        DisplayControl 对象

    Examples:
        >>> # 方式1：直接传递参数
        >>> display = create_display(text="错误消息", style="error")
        >>>
        >>> # 方式2：传递字典
        >>> config = {"text": "错误消息", "style": "error"}
        >>> display = create_display(**config)
    """
    return DisplayControl(**kwargs)


def create_error_display(**kwargs) -> DisplayControl:
    """创建错误显示的快捷函数"""
    kwargs.setdefault("style", "error")
    return DisplayControl(**kwargs)


def create_warning_display(**kwargs) -> DisplayControl:
    """创建警告显示的快捷函数"""
    kwargs.setdefault("style", "warning")
    return DisplayControl(**kwargs)


def create_success_display(**kwargs) -> DisplayControl:
    """创建成功显示的快捷函数"""
    kwargs.setdefault("style", "success")
    return DisplayControl(**kwargs)


def create_fatal_display(**kwargs) -> DisplayControl:
    """创建致命错误显示的快捷函数"""
    kwargs.setdefault("style", "fatal")
    return DisplayControl(**kwargs)


def create_critical_display(**kwargs) -> DisplayControl:
    """创建严重错误显示的快捷函数"""
    kwargs.setdefault("style", "critical")
    return DisplayControl(**kwargs)


def create_notice_display(**kwargs) -> DisplayControl:
    """创建通知显示的快捷函数"""
    kwargs.setdefault("style", "notice")
    return DisplayControl(**kwargs)
