"""
Base UI component class.

This module defines the abstract base class for all UI components.
Each component must implement at least the CLI rendering method.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseUIComponent(ABC):
    """
    Abstract base class for UI components.

    Each UI component must inherit from this class and implement
    the render_cli method. The render_web method is optional.
    """

    @abstractmethod
    def render_cli(self, data, renderer, **kwargs) -> Any:
        """
        Render the component for CLI interface (required).

        Args:
            data: The component data/control object
            renderer: The CLI renderer instance
            **kwargs: Additional parameters

        Returns:
            Rendered output (varies by component type)
        """
        pass

    def render_web(self, data, renderer, **kwargs):
        """
        Render the component for Web interface (optional).

        Args:
            data: The component data/control object
            renderer: The web renderer instance
            **kwargs: Additional parameters

        Returns:
            Rendered output (HTML or similar)

        Raises:
            NotImplementedError: If web rendering is not supported
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support web rendering"
        )
