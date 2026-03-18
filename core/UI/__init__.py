"""
Unified UI module for IntelliSearch.

This module provides a TUI system using Rich Layout.

Usage:
    from core.UI import UIEngine

    # Get renderer instance
    renderer = UIEngine.get_renderer()

    # Use convenience methods
    user_input = UIEngine.prompt_input("Enter your name:")

    # Get helper UIs
    welcome_ui = UIEngine.get_welcome_ui()
    tool_ui = UIEngine.get_tool_call_ui()

For custom components, import from core.UI.components:
    from core.UI.components import DisplayControl, InputControl, SelectControl, ConfirmControl
"""

# Main UI engine - the primary export
from core.UI.ui_engine import UIEngine

# Re-export as module-level attribute for convenience
__all__ = ["UIEngine"]
