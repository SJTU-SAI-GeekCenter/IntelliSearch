"""
Sequential Memory implementation for IntelliSearch.

This module provides a simple linear context management implementation
that maintains messages in the order they were added.
"""

import json
from typing import List, Dict, Any, Optional

from memory.base import BaseMemory
from core.logger import get_logger


class SequentialMemory(BaseMemory):
    """
    Sequential memory implementation for linear context management.

    This memory maintains entries in the order they were added and provides
    views compatible with LLM chat message formats.

    Attributes:
        system_prompt: Initial system prompt to include in memory
        entries: List of memory entries in chronological order
        logger: Logger instance

    Example:
        >>> memory = SequentialMemory(
        ...     system_prompt="You are a helpful assistant"
        ... )
        >>> memory.add({"role": "user", "content": "Hello"})
        >>> messages = memory.get_view("chat_messages")
        >>> print(len(memory))
        1
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the SequentialMemory.

        Args:
            system_prompt: Optional system prompt to initialize memory with
        """
        self.system_prompt = system_prompt
        self.entries: List[Dict[str, Any]] = []
        self.logger = get_logger(__name__)

        # Initialize with system prompt if provided
        if system_prompt:
            self.entries.append({"role": "system", "content": system_prompt})

    def reset(self) -> None:
        """
        Reset memory to initial state.

        Clears all entries but preserves the system prompt if it was set.
        """
        self.entries = []
        if self.system_prompt:
            self.entries.append({"role": "system", "content": self.system_prompt})
        self.logger.info("Memory reset")

    def add(self, entry: Any) -> None:
        """
        Add a single memory entry.

        Args:
            entry: A dictionary representing a memory entry
                   (e.g., {"role": "user", "content": "Hello"})
        """
        if not isinstance(entry, dict):
            raise TypeError(f"Entry must be a dict, got {type(entry).__name__}")

        self.entries.append(entry)
        self.logger.debug(f"Added entry: {entry.get('role', 'unknown')}")

    def add_many(self, entries: List[Any]) -> None:
        """
        Add multiple memory entries at once.

        Args:
            entries: List of memory entry dictionaries
        """
        for entry in entries:
            self.add(entry)
        self.logger.info(f"Added {len(entries)} entries")

    def get_view(self, view_type: str, **kwargs) -> Any:
        """
        Return a projected view of memory.

        Args:
            view_type: Type of view ("chat_messages" supported)
            **kwargs: Additional parameters (e.g., max_entries for truncation)

        Returns:
            List of entries in the requested format

        Raises:
            NotImplementedError: If view_type is not supported
        """
        if view_type == "chat_messages":
            max_entries = kwargs.get("max_entries")
            if max_entries and max_entries > 0:
                # Return last N entries, but always include system prompt
                system_entries = [e for e in self.entries if e.get("role") == "system"]
                other_entries = [e for e in self.entries if e.get("role") != "system"]
                return system_entries + other_entries[-max_entries:]
            return self.entries

        raise NotImplementedError(
            f"View type '{view_type}' is not implemented. "
            f"Supported types: ['chat_messages']"
        )

    def export(self) -> Any:
        """
        Export memory in serializable format.

        Returns:
            List of memory entries (JSON-serializable)
        """
        return json.dumps(self.entries, ensure_ascii=False, indent=2)

    def load(self, data: Any) -> None:
        """
        Load memory from serialized data.

        Args:
            data: JSON string or list of memory entries

        Raises:
            ValueError: If data format is invalid
        """
        try:
            if isinstance(data, str):
                entries = json.loads(data)
            elif isinstance(data, list):
                entries = data
            else:
                raise ValueError(
                    f"Data must be JSON string or list, got {type(data).__name__}"
                )

            if not isinstance(entries, list):
                raise ValueError("Parsed data must be a list")

            self.entries = entries
            self.logger.info(f"Loaded {len(entries)} entries from data")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}") from e

    def __len__(self) -> int:
        """
        Return the number of entries in memory.

        Returns:
            Number of memory entries
        """
        return len(self.entries)

    def get_last_n_messages(self, n: int) -> List[Dict[str, Any]]:
        """
        Get the last N messages (excluding system prompt).

        Args:
            n: Number of messages to retrieve

        Returns:
            List of the last N messages
        """
        non_system = [e for e in self.entries if e.get("role") != "system"]
        return non_system[-n:]

    def clear_history(self) -> None:
        """
        Clear all history except system prompt.

        Alias for reset() for compatibility with existing code.
        """
        self.reset()

    def append_history(
        self, history_episodes: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Append conversation episodes to history.

        Args:
            history_episodes: List of history dictionaries with 'role' and 'content'
        """
        if not history_episodes:
            return

        for episode in history_episodes:
            role = episode.get("role")
            if role and role in ("system", "user", "assistant", "tool"):
                self.add(episode)
            else:
                self.logger.error(f"Invalid role in history: {role}")
