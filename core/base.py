"""
Base agent abstraction for IntelliSearch system.

This module defines the abstract base class that all agent implementations
must inherit from, ensuring a consistent interface across different agent types.
"""

from abc import ABC, abstractmethod
from core.schema import AgentRequest, AgentResponse


class BaseAgent(ABC):
    """
    Abstract base class for all Agent implementations.

    This class defines the contract that all concrete agents must follow.
    It provides a unified interface for agent inference while allowing
    subclasses to implement their specific logic.

    Attributes:
        name: Human-readable name/identifier for the agent

    Example:
        >>> class MyAgent(BaseAgent):
        ...     def __init__(self):
        ...         super().__init__(name="MyCustomAgent")
        ...
        ...     def inference(self, request: AgentRequest) -> AgentResponse:
        ...         # Implementation here
        ...         return AgentResponse(
        ...             status="success",
        ...             answer="Response text",
        ...             metadata={}
        ...         )
    """

    def __init__(self, name: str):
        """
        Initialize the BaseAgent.

        Args:
            name: Human-readable name/identifier for this agent instance

        Raises:
            ValueError: If name is empty or None
        """
        if not name or not name.strip():
            raise ValueError("Agent name must be a non-empty string")

        self.name = name.strip()

    @abstractmethod
    def inference(self, request: AgentRequest) -> AgentResponse:
        """
        Execute the agent's inference logic.

        This method must be implemented by all concrete agent classes.
        It takes a unified request format and returns a unified response format.

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse containing status, answer, and optional metadata

        Raises:
            NotImplementedError: This method must be implemented by subclasses
            ValueError: If request is invalid or missing required fields
            RuntimeError: If inference execution fails

        Example:
            >>> request = AgentRequest(prompt="What is AI?")
            >>> response = agent.inference(request)
            >>> print(response.answer)
        """
        pass

    def __repr__(self) -> str:
        """Return string representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"
