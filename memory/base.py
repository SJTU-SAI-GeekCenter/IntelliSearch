"""
Base Memory abstraction for IntelliSearch.

This module provides abstract interfaces for memory management,
allowing different memory implementations to be plugged in.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMemory(ABC):
    """
    Abstract base class for memory management.

    BaseMemory is responsible for maintaining the agent's serializable
    context state and providing message views to the LLM.

    Example:
        >>> memory = SequentialMemory()
        >>> memory.add({"role": "user", "content": "Hello"})
        >>> messages = memory.get_view("chat_messages")
    """

    @abstractmethod
    def reset(self) -> None:
        """
        Reset memory to initial state.

        This method clears all memory entries and resets the memory
        to its initial configuration.
        """
        pass

    @abstractmethod
    def add(self, entry: Any) -> None:
        """
        Add a single memory entry.

        Args:
            entry: A structured memory entry (can be any type)
        """
        pass

    @abstractmethod
    def add_many(self, entries: List[Any]) -> None:
        """
        Add multiple memory entries at once.

        Args:
            entries: List of structured memory entries
        """
        pass

    @abstractmethod
    def get_view(self, view_type: str, **kwargs) -> Any:
        """
        Return a projected view of memory.

        This method allows different representations of the same memory
        to be returned based on the view_type parameter.

        Args:
            view_type: Type of view to return (e.g., "chat_messages")
            **kwargs: Additional parameters for view generation

        Returns:
            View of memory in the requested format

        Raises:
            NotImplementedError: If view_type is not supported
        """
        pass

    @abstractmethod
    def export(self) -> Any:
        """
        Export memory in serializable format.

        Returns:
            Serializable representation of memory
        """
        pass

    @abstractmethod
    def load(self, data: Any) -> None:
        """
        Load memory from serialized data.

        Args:
            data: Serialized memory data to load
        """
        pass

    def __len__(self) -> int:
        """
        Return the number of entries in memory.

        Returns:
            Number of memory entries
        """
        raise NotImplementedError("Subclasses must implement __len__")
