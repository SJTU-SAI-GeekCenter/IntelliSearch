"""
Base renderer interface for UI engine.

This module defines the abstract interface that all renderers must implement.
Both CLIRenderer and WebRenderer should inherit from BaseRenderer.
"""

from abc import ABC, abstractmethod
from typing import Optional
from core.UI.components import InputControl, SelectControl, ConfirmControl


class BaseRenderer(ABC):
    """
    Abstract base class for UI renderers.

    All renderer implementations (CLI, Web, etc.) must implement these methods
    to provide a consistent interface for user interactions.
    """

    @abstractmethod
    def prompt_input(self, control: InputControl) -> str:
        """
        Prompt user for text input.

        Args:
            control: Input control with message, placeholder, etc.

        Returns:
            User input string
        """
        pass

    @abstractmethod
    def prompt_select(self, control: SelectControl) -> str:
        """
        Prompt user to select an option.

        Args:
            control: Select control with options and default

        Returns:
            Selected option string
        """
        pass

    @abstractmethod
    def prompt_confirm(self, control: ConfirmControl) -> bool:
        """
        Prompt user for confirmation (yes/no).

        Args:
            control: Confirm control with message and title

        Returns:
            True if confirmed, False otherwise
        """
        pass

    def display(self, *args, **kwargs):
        """
        Display a message with default styling.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title, style)
        """
        pass

    def display_success(self, *args, **kwargs):
        """
        Display a success message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass

    def display_warning(self, *args, **kwargs):
        """
        Display a warning message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass

    def display_error(self, *args, **kwargs):
        """
        Display an error message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass

    def display_fatal(self, *args, **kwargs):
        """
        Display a fatal error message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass

    def display_critical(self, *args, **kwargs):
        """
        Display a critical error message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass

    def display_notice(self, *args, **kwargs):
        """
        Display a notice message.

        Args:
            *args: Variable arguments for message parts
            **kwargs: Optional parameters (e.g., title)
        """
        pass
