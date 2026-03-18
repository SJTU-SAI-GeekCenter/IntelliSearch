"""
Form control for multi-page dynamic forms.

This module provides a FormControl that can aggregate multiple
dynamic/static components (input/select/static) into a paginated flow.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from .base_component import BaseUIComponent
from .input import InputControl
from core.UI.theme import ThemeColors
from core.UI.live import (
    start_live,
    stop_live,
    set_live_layer,
    clear_live_layer,
    has_live_layers,
)

if TYPE_CHECKING:
    from core.UI.cli_renderer import CLIRenderer


@dataclass
class FormResult:
    """Result of form operation."""

    success: bool
    completed: bool
    title: str
    values: Dict[str, Any] = field(default_factory=dict)
    pages_total: int = 0
    page_results: List[Dict[str, Any]] = field(default_factory=list)
    cancelled: bool = False
    error: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        """Return JSON-serializable result."""
        return {
            "success": self.success,
            "completed": self.completed,
            "title": self.title,
            "values": self.values,
            "pages_total": self.pages_total,
            "page_results": self.page_results,
            "cancelled": self.cancelled,
            "error": self.error,
        }


@dataclass
class FormControl:
    """
    Multi-page dynamic form control.

    Attributes:
        title: Fixed title of the whole form
        pages: JSON list; each sub-list is one page; each element is one component
        allow_cancel: Whether user can cancel from navigation
    """

    title: str
    pages: List[List[Dict[str, Any]]]
    allow_cancel: bool = False

    def __post_init__(self):
        if not self.title:
            raise ValueError("title cannot be empty")
        if not isinstance(self.pages, list) or not self.pages:
            raise ValueError("pages must be a non-empty list")
        for i, page in enumerate(self.pages):
            if not isinstance(page, list):
                raise ValueError(f"pages[{i}] must be a list")

    def __rich__(self):
        """Render form summary as a Rich panel."""
        content = Text()
        content.append(self.title, style=Style(color=ThemeColors.PRIMARY, bold=True))
        content.append("\n")
        content.append(
            f"{len(self.pages)} pages, supported components: input / select / static",
            style=Style(color=ThemeColors.FG),
        )
        content.append("\n")
        content.append(
            "Each step uses a unified next/confirm flow", style=Style(dim=True)
        )

        return Panel(
            content,
            title="🧩 Dynamic Form",
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(0, 1),
        )


class FormComponent(BaseUIComponent):
    """Component for rendering multi-page FormControl."""

    _DYNAMIC_TYPES = {"input", "select"}

    def _build_step_panel(
        self,
        form_title: str,
        page_no: int,
        total_pages: int,
        message: str,
        description: str = "",
        widget_lines: Optional[List[str]] = None,
        error: str = "",
    ) -> Panel:
        """Build outer box panel for one dynamic step."""
        content = Text()
        content.append(f"Step {page_no}/{total_pages}", style=Style(dim=True))
        content.append("\n")
        if description:
            content.append_text(Text.from_markup(description))
            content.append("\n")
        if message:
            content.append(message, style=Style(color=ThemeColors.PRIMARY, bold=True))

        if widget_lines:
            content.append("\n\n")
            content.append("\n".join(widget_lines), style=Style(color=ThemeColors.FG))

        if error:
            content.append("\n\n")
            content.append(error, style=Style(color=ThemeColors.ERROR, bold=True))

        return Panel(
            content,
            title=form_title,
            title_align="right",
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(0, 1),
        )

    def _normalize_steps(
        self, pages: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize pages to strict one-dynamic-component-per-screen steps.

        Rule:
        - Each page must contain exactly one dynamic component (`input` or `select`)
        - Optional `static` items are treated as page description
        - Dynamic item may also provide `description`
        """
        steps: List[Dict[str, Any]] = []

        for idx, page in enumerate(pages, start=1):
            dynamic_items = [
                item
                for item in page
                if str(item.get("type", "")).strip().lower() in self._DYNAMIC_TYPES
            ]
            if len(dynamic_items) != 1:
                raise ValueError(
                    f"Page {idx} must contain exactly 1 dynamic component (input/select), got {len(dynamic_items)}"
                )

            dynamic_item = dynamic_items[0]
            dynamic_type = str(dynamic_item.get("type", "")).strip().lower()

            static_desc_list: List[str] = []
            for item in page:
                item_type = str(item.get("type", "")).strip().lower()
                if item_type == "static":
                    text = str(item.get("text", "")).strip()
                    if text:
                        static_desc_list.append(text)

            dynamic_desc = str(dynamic_item.get("description", "")).strip()
            if dynamic_desc:
                static_desc_list.append(dynamic_desc)

            steps.append(
                {
                    "page": idx,
                    "component": dynamic_item,
                    "type": dynamic_type,
                    "description": "\n".join(static_desc_list),
                }
            )

        return steps

    def _build_summary_text(self, values: Dict[str, Any]) -> str:
        """Build summary display content."""
        if not values:
            return "No selections to display."

        lines = ["[bold]Your selections:[/bold]"]
        for key, value in values.items():
            if isinstance(value, list):
                display_val = ", ".join(str(v) for v in value)
            else:
                display_val = str(value)
            lines.append(f"- [cyan]{key}[/cyan]: {display_val}")
        return "\n".join(lines)

    def _get_key(self) -> tuple[str, Optional[str]]:
        """Cross-platform key reading for TUI in box."""
        if os.name == "nt":
            import msvcrt

            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                ch2 = msvcrt.getwch()
                mapping = {"H": "up", "P": "down", "K": "left", "M": "right"}
                return mapping.get(ch2, "unknown"), None
            if ch in ("\r", "\n"):
                return "enter", None
            if ch == "\x08":
                return "backspace", None
            if ch == " ":
                return "space", None
            if ch == "\x03":
                raise KeyboardInterrupt
            return "char", ch

        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x1b":
                seq = ch + sys.stdin.read(2)
                mapping = {
                    "\x1b[A": "up",
                    "\x1b[B": "down",
                    "\x1b[C": "right",
                    "\x1b[D": "left",
                }
                return mapping.get(seq, "unknown"), None
            if ch in ("\r", "\n"):
                return "enter", None
            if ch in ("\x7f", "\b"):
                return "backspace", None
            if ch == " ":
                return "space", None
            return "char", ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _show_panel_live(self, panel: Panel) -> None:
        """Render one frame using global live."""
        set_live_layer("form", panel)

    def _run_input_step(
        self,
        form_title: str,
        page_no: int,
        total_pages: int,
        description: str,
        item: Dict[str, Any],
    ) -> str:
        """Run an input step fully inside one box."""
        key = item.get("key")
        message = str(item.get("message", key or "Please enter a value"))
        default_value = str(item.get("default_value", ""))
        control = InputControl(
            message=message,
            placeholder=item.get("placeholder", ""),
            default_value=default_value,
            min_length=int(item.get("min_length", 0)),
            max_length=int(item.get("max_length", 1000)),
            password=bool(item.get("password", False)),
            multiline=bool(item.get("multiline", False)),
        )

        current = default_value
        error_msg = ""

        while True:
            display_value = "*" * len(current) if control.password else current
            widget_lines = []
            if control.placeholder:
                widget_lines.append(f"Hint: {control.placeholder}")
            widget_lines.append(f"Input: {display_value}")
            widget_lines.append("Actions: Enter confirm / Backspace delete")

            panel = self._build_step_panel(
                form_title=form_title,
                page_no=page_no,
                total_pages=total_pages,
                message=message,
                description=description,
                widget_lines=widget_lines,
                error=error_msg,
            )
            self._show_panel_live(panel)

            key_type, key_char = self._get_key()
            if key_type == "enter":
                valid, err = control.validate(current)
                if valid:
                    return current
                error_msg = f"Invalid input: {err}"
                continue
            if key_type == "backspace":
                current = current[:-1]
                error_msg = ""
                continue
            if key_type == "char" and key_char:
                if len(current) < control.max_length:
                    current += key_char
                error_msg = ""

    def _run_select_step(
        self,
        form_title: str,
        page_no: int,
        total_pages: int,
        description: str,
        message: str,
        options: List[str],
        allow_multiple: bool,
        default_index: int = 0,
        default_indices: Optional[List[int]] = None,
    ) -> Any:
        """Run a select step fully inside one box."""
        if not options:
            raise ValueError("select options cannot be empty")

        curr_idx = default_index if 0 <= default_index < len(options) else 0
        selected = set(default_indices or ([] if not allow_multiple else [curr_idx]))

        while True:
            widget_lines: List[str] = []
            for i, opt in enumerate(options):
                cursor = ">" if i == curr_idx else " "
                if allow_multiple:
                    mark = "✓" if i in selected else " "
                    widget_lines.append(f"{cursor} [{mark}] {opt}")
                else:
                    widget_lines.append(f"{cursor} {opt}")

            if allow_multiple:
                widget_lines.append("")
                widget_lines.append("Actions: ↑↓ move / Space toggle / Enter confirm")
            else:
                widget_lines.append("")
                widget_lines.append("Actions: ↑↓ move / Enter confirm")

            panel = self._build_step_panel(
                form_title=form_title,
                page_no=page_no,
                total_pages=total_pages,
                message=message,
                description=description,
                widget_lines=widget_lines,
            )
            self._show_panel_live(panel)

            key_type, _ = self._get_key()
            if key_type == "up":
                curr_idx = (curr_idx - 1) % len(options)
                continue
            if key_type == "down":
                curr_idx = (curr_idx + 1) % len(options)
                continue
            if key_type == "space" and allow_multiple:
                if curr_idx in selected:
                    selected.remove(curr_idx)
                else:
                    selected.add(curr_idx)
                continue
            if key_type == "enter":
                if allow_multiple:
                    indices = sorted(selected)
                    return [options[i] for i in indices]
                return options[curr_idx]

    def render_cli(
        self, data: FormControl, renderer: "CLIRenderer", mode: str = "tui", **kwargs
    ) -> FormResult:
        """Render sequential single-dynamic-step form and return JSON-like result."""
        steps = self._normalize_steps(data.pages)
        total_pages = len(steps)
        values: Dict[str, Any] = {}
        page_results: List[Dict[str, Any]] = []

        try:
            start_live()
            while True:
                values = {}
                page_results = []

                for idx, step in enumerate(steps, start=1):
                    item = step["component"]
                    item_type = step["type"]
                    description = step["description"]

                    if item_type == "input":
                        key = item.get("key")
                        if not key:
                            raise ValueError(
                                f"Input component on page {idx} is missing required key"
                            )
                        input_value = self._run_input_step(
                            form_title=data.title,
                            page_no=idx,
                            total_pages=total_pages,
                            description=description,
                            item=item,
                        )
                        values[key] = input_value
                        page_results.append(
                            {
                                "page": idx,
                                "values": {key: input_value},
                                "description": description,
                            }
                        )
                        continue

                    if item_type == "select":
                        key = item.get("key")
                        if not key:
                            raise ValueError(
                                f"Select component on page {idx} is missing required key"
                            )

                        options = item.get("options", [])
                        if not isinstance(options, list) or not options:
                            raise ValueError(
                                f"Select component '{key}' on page {idx} has invalid or empty options"
                            )

                        allow_multiple = bool(item.get("allow_multiple", False))
                        selected_value = self._run_select_step(
                            form_title=data.title,
                            page_no=idx,
                            total_pages=total_pages,
                            description=description,
                            message=item.get("message", key),
                            options=options,
                            allow_multiple=allow_multiple,
                            default_index=int(item.get("default_index", 0)),
                            default_indices=item.get("default_indices"),
                        )

                        values[key] = selected_value
                        page_results.append(
                            {
                                "page": idx,
                                "values": {key: selected_value},
                                "description": description,
                            }
                        )
                        continue

                    raise ValueError(f"Unsupported dynamic component type: {item_type}")

                # 全部完成后，展示结果并让用户确认/重新选择
                summary_text = self._build_summary_text(values)
                summary_panel = Panel(
                    Text.from_markup(summary_text),
                    title=f"{data.title} · Review",
                    title_align="right",
                    border_style=Style(color=ThemeColors.SUCCESS),
                    padding=(0, 1),
                )
                self._show_panel_live(summary_panel)

                action = self._run_select_step(
                    form_title=f"{data.title} · Review",
                    page_no=total_pages,
                    total_pages=total_pages,
                    description=summary_text,
                    message="Choose action",
                    options=["Confirm", "Redo"],
                    allow_multiple=False,
                    default_index=0,
                )

                if action == "Redo":
                    continue

                return FormResult(
                    success=True,
                    completed=True,
                    title=data.title,
                    values=values,
                    pages_total=total_pages,
                    page_results=page_results,
                    cancelled=False,
                )

        except KeyboardInterrupt:
            return FormResult(
                success=False,
                completed=False,
                title=data.title,
                values=values,
                pages_total=total_pages,
                page_results=page_results,
                cancelled=True,
                error="Interrupted by user",
            )
        except Exception as e:
            return FormResult(
                success=False,
                completed=False,
                title=data.title,
                values=values,
                pages_total=total_pages,
                page_results=page_results,
                cancelled=False,
                error=str(e),
            )
        finally:
            clear_live_layer("form")
            if not has_live_layers():
                stop_live()


# ============ 工厂函数 ============


def create_form(**kwargs) -> FormControl:
    """
    创建 FormControl 对象的工厂函数。

    Args:
        title: 表单固定标题
        pages: JSON 列表，每个子列表代表一页组件
        allow_cancel: 是否允许取消

    Returns:
        FormControl 对象
    """
    return FormControl(**kwargs)
