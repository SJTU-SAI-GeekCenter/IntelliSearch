"""
Unified UI engine for IntelliSearch.

This module provides a unified UI system that combines:
1. Auto-detection of runtime environment (CLI/Web)
2. Automatic renderer selection
3. TUI layout management using Rich
"""

import sys
from typing import Any, Optional
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from core.UI.theme import ThemeColors
from core.UI.base_renderer import BaseRenderer
from core.UI.cli_renderer import CLIRenderer
from core.UI.web_renderer import WebRenderer
from core.exceptions import ErrorSeverity


class UIEngine:
    """
    Unified UI engine that provides automatic renderer selection and TUI layout management.

    This class:
    - Automatically detects the runtime environment (terminal vs web)
    - Selects the appropriate renderer (CLI or Web)
    - Provides TUI layout management using VerticalLiveLayout
    - Supports component auto-registration to unified layout

    Example:
        >>> # Auto-detect and get renderer
        >>> renderer = UIEngine.get_renderer()
        >>>
        >>> # Use convenience methods
        >>> user_input = UIEngine.prompt_input("Enter your name:")
        >>>
        >>> # Register components to unified layout
        >>> UIEngine.register_component_region("header", position="top", size=3)
        >>> UIEngine.register_component_region("main", position="bottom")
        >>> UIEngine.start_vertical_layout()
        >>>
        >>> # Update component regions
        >>> UIEngine.update_component_region("main", new_content)
    """

    # Layout and Live instances for TUI (legacy, kept for compatibility)
    _layout = None

    # Auto-detected renderer
    _renderer = None

    # VerticalLiveLayout instance for unified layout management (legacy)
    _vertical_layout: Any | None = None

    @classmethod
    def _detect_environment(cls) -> BaseRenderer:
        """
        Detect runtime environment and return appropriate renderer.

        Returns:
            CLIRenderer if running in terminal, WebRenderer otherwise
        """
        # Check if running in a terminal
        if sys.stdin.isatty():
            return CLIRenderer()
        else:
            # Not a TTY - assume web environment
            return WebRenderer()

    @classmethod
    def get_renderer(cls) -> BaseRenderer:
        """
        Get or create the appropriate renderer instance.

        Returns:
            Active renderer (CLI or Web) based on environment
        """
        if cls._renderer is None:
            cls._renderer = cls._detect_environment()
        return cls._renderer

    @classmethod
    def get_console(cls) -> Console:
        """
        Get the global Rich Console instance.

        Returns:
            Console instance from core.UI.console
        """
        from core.UI.console import console

        return console

    @classmethod
    def get_vertical_layout(cls) -> Any:
        """
        Get or create the VerticalLiveLayout instance.

        Returns:
            VerticalLiveLayout singleton instance
        """
        raise NotImplementedError("VerticalLiveLayout is not yet implemented")

    @classmethod
    def create_base_layout(cls) -> Layout:
        """
        Create a base TUI layout with header, main, and footer.

        Returns:
            Layout instance with header, main, and footer regions
        """
        layout = Layout()

        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=2),
        )

        return layout

    @classmethod
    def update_region(cls, region_name: str, content):
        """
        Update a specific region in the layout.

        Args:
            region_name: Name of the region to update (e.g., "main", "header")
            content: Rich renderable to display
        """
        if cls._layout is not None and region_name in cls._layout:
            cls._layout[region_name].update(content)

    @classmethod
    def clear_region(cls, region_name: str):
        """
        Clear a specific region in the layout.

        Args:
            region_name: Name of the region to clear
        """
        if cls._layout is not None and region_name in cls._layout:
            cls._layout[region_name].update("")

    @classmethod
    def print(cls, content):
        """
        Print content directly to console (for simple CLI mode).

        Args:
            content: Rich renderable to print
        """
        cls.get_console().print(content)

    @classmethod
    def prompt_input(
        cls, input_control=None, message: Optional[str] = None, **kwargs
    ) -> str:
        """
        Prompt user for input.

        Supports three calling methods:
        1. UIEngine.prompt_input(message="Enter username", min_length=3)
        2. UIEngine.prompt_input(**{"message": "Enter username", "min_length": 3})
        3. UIEngine.prompt_input(InputControl(...))

        Args:
            input_control: InputControl object (optional)
            message: Prompt message
            **kwargs: Additional parameters for InputControl or complete config dict

        Returns:
            User input string

        Examples:
            >>> # Method 1: Pass parameters directly
            >>> name = UIEngine.prompt_input(message="Enter username", min_length=3)
            >>>
            >>> # Method 2: Pass dict/JSON
            >>> config = {"message": "Enter password", "password": True}
            >>> password = UIEngine.prompt_input(**config)
            >>>
            >>> # Method 3: Pass Control object
            >>> from core.UI.components import InputControl
            >>> control = InputControl(message="Enter email")
            >>> email = UIEngine.prompt_input(control)
        """
        from core.UI.components import InputControl

        if input_control is not None:
            control = input_control
        else:
            control = InputControl(message=message or "", **kwargs)
        return cls.get_renderer().prompt_input(control)

    @classmethod
    def prompt_select(
        cls,
        select_control=None,
        message: Optional[str] = None,
        options: Optional[list] = None,
        **kwargs,
    ) -> str:
        """
        Prompt user to select an option.

        Supports three calling methods:
        1. UIEngine.prompt_select(message="Select color", options=["Red", "Blue", "Green"])
        2. UIEngine.prompt_select(**{"message": "Select", "options": ["A", "B", "C"], "allow_multiple": True})
        3. UIEngine.prompt_select(SelectControl(...))

        Args:
            select_control: SelectControl object (optional)
            message: Prompt message
            options: List of options to choose from
            **kwargs: Additional parameters for SelectControl or complete config dict

        Returns:
            Selected option string

        Examples:
            >>> # Method 1: Pass parameters directly
            >>> color = UIEngine.prompt_select(message="Select color", options=["Red", "Blue", "Green"])
            >>>
            >>> # Method 2: Pass dict/JSON
            >>> config = {"message": "Select", "options": ["A", "B", "C"], "allow_multiple": True}
            >>> result = UIEngine.prompt_select(**config)
            >>>
            >>> # Method 3: Pass Control object
            >>> from core.UI.components import SelectControl
            >>> control = SelectControl(message="Select", options=["A", "B", "C"])
            >>> result = UIEngine.prompt_select(control)
        """
        from core.UI.components import SelectControl

        if select_control is not None:
            control = select_control
        else:
            control = SelectControl(
                message=message or "", options=options or [], **kwargs
            )
        return cls.get_renderer().prompt_select(control)

    @classmethod
    def prompt_confirm(
        cls, confirm_control=None, message: Optional[str] = None, **kwargs
    ) -> bool:
        """
        Prompt user for confirmation.

        Supports three calling methods:
        1. UIEngine.prompt_confirm(message="Are you sure you want to delete?")
        2. UIEngine.prompt_confirm(**{"message": "Are you sure you want to delete?", "default_choice": False})
        3. UIEngine.prompt_confirm(ConfirmControl(...))

        Args:
            confirm_control: ConfirmControl object (optional)
            message: Confirmation message
            **kwargs: Additional parameters for ConfirmControl or complete config dict

        Returns:
            True if confirmed, False otherwise

        Examples:
            >>> # Method 1: Pass parameters directly
            >>> confirmed = UIEngine.prompt_confirm(message="Are you sure you want to delete the file?")
            >>>
            >>> # Method 2: Pass dict/JSON
            >>> config = {"message": "Are you sure you want to continue?", "title": "Dangerous Operation Confirmation"}
            >>> confirmed = UIEngine.prompt_confirm(**config)
            >>>
            >>> # Method 3: Pass Control object
            >>> from core.UI.components import ConfirmControl
            >>> control = ConfirmControl(message="Are you sure you want to continue?")
            >>> confirmed = UIEngine.prompt_confirm(control)
        """
        from core.UI.components import ConfirmControl

        if confirm_control is not None:
            control = confirm_control
        else:
            control = ConfirmControl(message=message or "", **kwargs)
        return cls.get_renderer().prompt_confirm(control)

    @classmethod
    def prompt_form(
        cls,
        form_control=None,
        title: Optional[str] = None,
        pages: Optional[list] = None,
        **kwargs,
    ) -> dict:
        """
        Prompt user with a multi-page dynamic form.

        Supports three calling methods:
        1. UIEngine.prompt_form(title="用户信息", pages=[[...], [...]])
        2. UIEngine.prompt_form(**{"title": "用户信息", "pages": [[...], [...]], "allow_cancel": True})
        3. UIEngine.prompt_form(FormControl(...))

        Args:
            form_control: FormControl object (optional)
            title: Fixed form title
            pages: JSON list, each sub-list is one page of components
            **kwargs: Additional FormControl parameters

        Returns:
            JSON-like dictionary result
        """
        from core.UI.components import FormControl

        if form_control is not None:
            control = form_control
        else:
            control = FormControl(
                title=title or "动态表单",
                pages=pages or [],
                **kwargs,
            )

        renderer = cls.get_renderer()
        return renderer.prompt_form(control)

    @classmethod
    def get_welcome_ui(cls):
        """
        Get a WelcomeUI instance for the current environment.

        Returns:
            WelcomeUI instance appropriate for the current renderer
        """
        from core.UI.components import WelcomeUI

        return WelcomeUI()

    @classmethod
    def get_tool_call_ui(cls):
        """
        Get a ToolCallUI instance for the current environment.

        Returns:
            ToolCallUI instance appropriate for the current renderer
        """
        from core.UI.components import ToolCallUI

        return ToolCallUI()

    @classmethod
    def register_component_region(
        cls,
        region_name: str,
        position: str = "bottom",
        size: Optional[int] = None,
        content=None,
    ):
        """
        Register a UI component to the vertical layout.

        This is the recommended way for components to register their display regions.
        Components can call this method during initialization to automatically
        register their regions to the unified layout.

        Args:
            region_name: Unique identifier for this component's region
            position: Where to insert the region ("top", "bottom", "after:X", "before:X", or index)
            size: Fixed height for this region (None for auto-sizing)
            content: Initial content for the region (optional)

        Examples:
            >>> # Component can register its region during initialization
            >>> UIEngine.register_component_region(
            ...     "tool_status",
            ...     position="bottom",
            ...     size=3,
            ...     content=Panel("Ready")
            ... )
        """
        layout = cls.get_vertical_layout()
        try:
            layout.add_region(
                region_name, position=position, size=size, content=content
            )
        except ValueError:
            # Region already exists, just update content
            if content is not None:
                layout.update_region(region_name, content)

    @classmethod
    def update_component_region(cls, region_name: str, content):
        """
        Update content for a registered component region.

        Args:
            region_name: Name of the region to update
            content: New content to display (Rich renderable)

        Examples:
            >>> UIEngine.update_component_region(
            ...     "tool_status",
            ...     Panel("Processing...")
            ... )
        """
        layout = cls.get_vertical_layout()
        layout.update_region(region_name, content)

    @classmethod
    def start_vertical_layout(cls, refresh_per_second: int = 4):
        """
        Start the vertical layout live display (legacy, uses VerticalLiveLayout).

        Args:
            refresh_per_second: Refresh rate for live updates

        Examples:
            >>> # Register component regions first
            >>> UIEngine.register_component_region("header", position="top", size=3)
            >>> UIEngine.register_component_region("main", position="bottom")
            >>>
            >>> # Then start the live display
            >>> UIEngine.start_vertical_layout()
        """
        layout = cls.get_vertical_layout()
        layout.set_console(cls.get_console())
        layout.start(refresh_per_second=refresh_per_second)

    @classmethod
    def stop_vertical_layout(cls):
        """Stop the vertical layout live display (legacy)."""
        layout = cls.get_vertical_layout()
        layout.stop()

    @classmethod
    def display(cls, *args, **kwargs):
        """
        Display a message with default styling using the current renderer.

        Supports three calling methods:
        1. UIEngine.display("Message content") - Pass text directly
        2. UIEngine.display(DisplayControl(...)) - Pass DisplayControl object
        3. UIEngine.display(**{"text": "Message", "style": "error"}) - Pass dict/JSON

        Args:
            *args: Text parts to display (supports Rich formatting), or a DisplayControl object
            **kwargs: Optional parameters (e.g., title) or complete config dict

        Examples:
            >>> # Method 1: Pass text directly
            >>> UIEngine.display("This is a message")
            >>>
            >>> # Method 2: Use DisplayControl object
            >>> from core.UI.components import DisplayControl
            >>> display = DisplayControl(text="Error message", style="error")
            >>> UIEngine.display(display)
            >>>
            >>> # Method 3: Pass dict/JSON
            >>> UIEngine.display(**{"text": "Error message", "style": "error"})
        """
        from core.UI.components import DisplayControl

        # Check if first argument is a DisplayControl
        if args and isinstance(args[0], DisplayControl):
            display_control = args[0]
            # Use the DisplayControl's style and parameters
            style = display_control.style
            text = display_control.text

            # Map DisplayControl styles to display methods
            if style == "fatal":
                cls.display_fatal(text, title=display_control.title)
            elif style == "critical":
                cls.display_critical(text, title=display_control.title)
            elif style == "error":
                cls.display_error(text, title=display_control.title)
            elif style == "warning":
                cls.display_warning(text, title=display_control.title)
            elif style == "notice":
                cls.display_notice(text, title=display_control.title)
            elif style == "success":
                cls.display_success(text, title=display_control.title)
            else:  # info or default
                cls.get_renderer().display(text, title=display_control.title)
        elif kwargs and "text" in kwargs:
            # 方式3：传递字典/JSON
            display_control = DisplayControl(**kwargs)
            # 递归调用以处理DisplayControl
            cls.display(display_control)
        else:
            # 方式1：默认行为
            cls.get_renderer().display(*args, **kwargs)

    @classmethod
    def display_success(cls, *args, **kwargs):
        """
        Display a success message using the current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_success(*args, **kwargs)

    @classmethod
    def display_warning(cls, *args, **kwargs):
        """
        Display a warning message using the current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_warning(*args, **kwargs)

    @classmethod
    def display_error(cls, *args, **kwargs):
        """
        Display an error message using the current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_error(*args, **kwargs)

    @classmethod
    def display_fatal(cls, *args, **kwargs):
        """
        Display a fatal error message using the current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_fatal(*args, **kwargs)

    @classmethod
    def display_critical(cls, *args, **kwargs):
        """
        Display a critical error message using the current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_critical(*args, **kwargs)

    @classmethod
    def display_notice(cls, *args, **kwargs):
        """
        Display a notice message using current renderer.

        Args:
            *args: Text parts to display (supports Rich formatting like [dim], [bold])
            **kwargs: Optional parameters (e.g., title)
        """
        cls.get_renderer().display_notice(*args, **kwargs)

    @classmethod
    def display_exception(cls, error_input):
        """
        Display exception to UI

        Supports two calling methods:
        1. Pass error code string directly: UIEngine.display_exception("MCP_001")
        2. Pass exception object: UIEngine.display_exception(exception)

        Args:
            error_input: Error code string (e.g., "MCP_001") or exception object

        Examples:
            >>> # Method 1: Pass error code directly
            >>> UIEngine.display_exception("MCP_001")
            >>>
            >>> # Method 2: Pass exception object
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     UIEngine.display_exception(e)
        """
        from core.error_center import get_error_by_code
        from core.exceptions import IntelliSearchError

        # If string, treat as error code
        if isinstance(error_input, str):
            error_info = get_error_by_code(error_input)
            if error_info is None:
                cls.display_error(f"Unknown error code: {error_input}")
                return

            # Select display method based on severity level
            severity = error_info["severity"]
            message = error_info["description"]
            suggestions = error_info.get("suggestions", "")

            # Combine message
            full_message = f"[{error_input}] {message}"
            if suggestions:
                full_message += f"\n💡 Suggestion: {suggestions}"

            # Call corresponding display method
            if severity == ErrorSeverity.FATAL:
                cls.display_fatal(full_message)
            elif severity == ErrorSeverity.CRITICAL:
                cls.display_critical(full_message)
            elif severity == ErrorSeverity.ERROR:
                cls.display_error(full_message)
            elif severity == ErrorSeverity.WARNING:
                cls.display_warning(full_message)
            elif severity == ErrorSeverity.NOTICE:
                cls.display_notice(full_message)
            else:
                cls.display(full_message)

        # If exception object
        elif isinstance(error_input, Exception):
            # Format exception message
            if isinstance(error_input, IntelliSearchError):
                # IntelliSearchError already has complete format
                message = error_input.format_user_message()
                severity = error_input.severity
            else:
                # Native exception, simple format
                message = f"{type(error_input).__name__}: {error_input}"
                severity = ErrorSeverity.ERROR

            # Select display method based on severity level
            if severity == ErrorSeverity.FATAL:
                cls.display_fatal(message)
            elif severity == ErrorSeverity.CRITICAL:
                cls.display_critical(message)
            elif severity == ErrorSeverity.ERROR:
                cls.display_error(message)
            elif severity == ErrorSeverity.WARNING:
                cls.display_warning(message)
            elif severity == ErrorSeverity.NOTICE:
                cls.display_notice(message)
            else:
                cls.display(message)

        # Other types
        else:
            cls.display_error(f"Invalid error input: {error_input}")
