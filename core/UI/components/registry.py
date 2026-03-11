"""
Component registry for UI components.

This module provides a registry system for registering and
retrieving UI components by their control type.
"""

from typing import Dict, Type, Any
from .base_component import BaseUIComponent


class ComponentRegistry:
    """
    Registry for UI components.

    This class manages the mapping between control types and their
    corresponding component classes.
    """

    def __init__(self):
        """Initialize the registry."""
        self._registry: Dict[str, Type[BaseUIComponent]] = {}

    def register(self, control_type: str, component_class: Type[BaseUIComponent]):
        """
        Register a component class for a control type.

        Args:
            control_type: The type of control (e.g., "display", "input")
            component_class: The component class to register
        """
        if not issubclass(component_class, BaseUIComponent):
            raise ValueError(f"{component_class} must inherit from BaseUIComponent")

        self._registry[control_type] = component_class

    def get(self, control_type: str) -> Type[BaseUIComponent]:
        """
        Get the component class for a control type.

        Args:
            control_type: The type of control

        Returns:
            The component class

        Raises:
            KeyError: If no component is registered for the control type
        """
        if control_type not in self._registry:
            raise KeyError(f"No component registered for control type: {control_type}")

        return self._registry[control_type]

    def has(self, control_type: str) -> bool:
        """
        Check if a component is registered for a control type.

        Args:
            control_type: The type of control

        Returns:
            True if registered, False otherwise
        """
        return control_type in self._registry

    def list_registered(self) -> Dict[str, Type[BaseUIComponent]]:
        """
        Get all registered components.

        Returns:
            Dictionary of control type to component class mappings
        """
        return self._registry.copy()


# Global registry instance
_registry = ComponentRegistry()


def register_component(control_type: str, component_class: Type[BaseUIComponent]):
    """
    Register a component class for a control type.

    Args:
        control_type: The type of control (e.g., "display", "input")
        component_class: The component class to register
    """
    _registry.register(control_type, component_class)


def get_component(control_type: str) -> Type[BaseUIComponent]:
    """
    Get the component class for a control type.

    Args:
        control_type: The type of control

    Returns:
        The component class
    """
    return _registry.get(control_type)


def register_default_components():
    """
    Register all default UI components.

    This function is called automatically when the module is imported.
    """
    from .display import (
        DisplayComponent,
        DisplaySuccessComponent,
        DisplayWarningComponent,
        DisplayErrorComponent,
    )
    from .input import InputComponent
    from .select import SelectComponent
    from .confirm import ConfirmComponent

    # Register display components
    register_component("display", DisplayComponent)
    register_component("display_success", DisplaySuccessComponent)
    register_component("display_warning", DisplayWarningComponent)
    register_component("display_error", DisplayErrorComponent)

    # Register input component
    register_component("input", InputComponent)

    # Register select component
    register_component("select", SelectComponent)

    # Register confirm component
    register_component("confirm", ConfirmComponent)


# Auto-register default components
register_default_components()
