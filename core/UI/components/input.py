"""
Input control for text input fields.

This module provides the InputControl for collecting
user text input in various formats.
"""

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
class InputControl:
    """
    Text input control.

    Attributes:
        message: Prompt message
        placeholder: Placeholder text
        default_value: Default value
        min_length: Minimum length
        max_length: Maximum length
        password: Whether to mask input
        multiline: Whether to allow multiple lines
    """

    message: str
    placeholder: str = ""
    default_value: str = ""
    min_length: int = 0
    max_length: int = 1000
    password: bool = False
    multiline: bool = False

    def __post_init__(self):
        """Validate input parameters."""
        if self.min_length < 0:
            raise ValueError("min_length must be non-negative")
        if self.max_length < self.min_length:
            raise ValueError("max_length must be >= min_length")

    def __rich__(self):
        """
        Render as a Rich renderable.

        Returns:
            Rich Panel showing input prompt
        """
        # Build content
        content = Text()

        # Add message
        content.append(self.message, style=Style(color=ThemeColors.PRIMARY, bold=True))
        content.append("\n")

        # Add placeholder if provided
        if self.placeholder:
            content.append(f"提示: {self.placeholder}", style=Style(dim=True))
            content.append("\n")

        # Add default value if provided
        if self.default_value:
            if self.password:
                display_value = "*" * len(self.default_value)
            else:
                display_value = self.default_value
            content.append(
                f"默认: {display_value}", style=Style(color=ThemeColors.INFO)
            )
            content.append("\n")

        # Add constraints if not default
        if self.min_length > 0 or self.max_length < 1000:
            constraints = []
            if self.min_length > 0:
                constraints.append(f"最少 {self.min_length} 字符")
            if self.max_length < 1000:
                constraints.append(f"最多 {self.max_length} 字符")
            if constraints:
                content.append(f"限制: {', '.join(constraints)}", style=Style(dim=True))

        return Panel(
            content,
            title="📝 输入",
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(0, 1),
        )

    def validate(self, value: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validate user input.

        Args:
            value: The user input to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            value = ""

        if len(value) < self.min_length:
            return False, f"Input must be at least {self.min_length} characters"
        if len(value) > self.max_length:
            return False, f"Input must be at most {self.max_length} characters"
        return True, None


class InputComponent(BaseUIComponent):
    """Component for rendering InputControl to CLI."""

    def render_cli(self, data: InputControl, renderer: "CLIRenderer", **kwargs) -> str:
        """
        Render input control in CLI mode.

        Args:
            data: InputControl instance
            renderer: CLI renderer instance
            **kwargs: Additional parameters

        Returns:
            User input string
        """
        if not renderer.is_available():
            # Basic fallback
            print(f"{data.message}")
            if data.placeholder:
                print(f"(提示: {data.placeholder})")
            if data.default_value:
                print(f"(默认: {data.default_value})")
            result = input("> ")
            return result if result else data.default_value

        # Use Rich prompt
        from rich.prompt import Prompt

        if data.password:
            from rich.prompt import Prompt

            result = Prompt.ask(
                data.message,
                default=data.default_value if data.default_value else "",
                password=True,
            )
        elif data.multiline:
            print(f"{data.message}")
            if data.placeholder:
                print(f"(提示: {data.placeholder})")
            lines = []
            while True:
                line = input("> ")
                if line == "":
                    break
                lines.append(line)
            result = "\n".join(lines)
        else:
            result = Prompt.ask(
                data.message,
                default=data.default_value if data.default_value else "",
            )

        # Ensure result is never None
        if result is None:
            result = ""

        # Validate
        is_valid, error_msg = data.validate(result)
        if not is_valid:
            renderer.display_error(f"验证失败: {error_msg}")
            return data.default_value or ""

        return result


# ============ 工厂函数 ============


def create_input(**kwargs) -> InputControl:
    """
    创建 InputControl 对象的工厂函数。

    支持两种调用方式：
    1. 直接传递参数：create_input(message="请输入用户名")
    2. 传递字典/JSON：create_input(**{"message": "请输入用户名"})

    Args:
        message: 提示消息
        placeholder: 占位符文本
        default_value: 默认值
        min_length: 最小长度
        max_length: 最大长度
        password: 是否隐藏输入
        multiline: 是否允许多行输入

    Returns:
        InputControl 对象

    Examples:
        >>> # 方式1：直接传递参数
        >>> input_ctrl = create_input(message="请输入用户名", min_length=3)
        >>>
        >>> # 方式2：传递字典
        >>> config = {"message": "请输入密码", "password": True}
        >>> input_ctrl = create_input(**config)
    """
    return InputControl(**kwargs)
