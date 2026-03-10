"""
UI Components module.

This module provides all UI controls and components that can be used in blocks.
Each control is self-contained with its rendering logic for both CLI and Web interfaces.

Components are automatically registered when this module is imported.
"""

from .display import (
    DisplayControl,
    DisplayStyle,
    DisplayComponent,
    DisplaySuccessComponent,
    DisplayWarningComponent,
    DisplayErrorComponent,
    DisplayFatalComponent,
    DisplayCriticalComponent,
    DisplayNoticeComponent,
    create_display,
    create_error_display,
    create_success_display,
    create_warning_display,
    create_fatal_display,
    create_critical_display,
    create_notice_display,
)
from .input import InputControl, InputComponent, create_input
from .select import (
    SelectControl,
    SelectResult,
    SelectComponent,
    TUISelectControl,
    create_select,
)
from .confirm import ConfirmControl, ConfirmResult, ConfirmComponent, create_confirm
from .base_component import BaseUIComponent
from .registry import (
    ComponentRegistry,
    register_component,
    get_component,
    register_default_components,
)
from .welcome import WelcomeUI
from .tool_call import ToolCallUI
from .loading import LoadingPanel, LoadingState, create_loading_panel

__all__ = [
    # Base
    "BaseUIComponent",
    # Display Controls and Components
    "DisplayControl",
    "DisplayStyle",
    "DisplayComponent",
    "DisplaySuccessComponent",
    "DisplayWarningComponent",
    "DisplayErrorComponent",
    "DisplayFatalComponent",
    "DisplayCriticalComponent",
    "DisplayNoticeComponent",
    # Display Factory Functions
    "create_display",
    "create_error_display",
    "create_success_display",
    "create_warning_display",
    "create_fatal_display",
    "create_critical_display",
    "create_notice_display",
    # Input Controls and Components
    "InputControl",
    "InputComponent",
    # Input Factory Functions
    "create_input",
    # Select Controls and Components
    "SelectControl",
    "SelectResult",
    "SelectComponent",
    "TUISelectControl",
    # Select Factory Functions
    "create_select",
    # Confirm Controls and Components
    "ConfirmControl",
    "ConfirmResult",
    "ConfirmComponent",
    # Confirm Factory Functions
    "create_confirm",
    # Registry
    "ComponentRegistry",
    "register_component",
    "get_component",
    "register_default_components",
    # UI Helpers
    "WelcomeUI",
    "ToolCallUI",
    # Loading
    "LoadingPanel",
    "LoadingState",
    "create_loading_panel",
]
