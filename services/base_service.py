"""
Base service abstraction for IntelliSearch backend services.

This module defines the abstract base class that all service implementations
must inherit from, ensuring a consistent interface across different service types.
"""

from abc import ABC, abstractmethod
from typing import Callable, List
from core.schema import AgentRequest, AgentResponse
from core.factory import AgentFactory
from core.logger import get_logger


# Type alias for status callback
StatusCallback = Callable[[str, str], None]


class BaseService(ABC):
    """
    Abstract base class for all backend service implementations.

    This class defines the contract that all concrete services must follow.
    It provides a unified interface for agent management and request processing
    while being completely decoupled from UI implementation.

    Services are responsible for:
    - Agent lifecycle management (creation, configuration)
    - Request/response processing orchestration
    - Status callback registration and notification
    - Error handling and logging

    Attributes:
        agent: The managed agent instance
        agent_type: Type identifier of the agent
        status_callbacks: List of registered status callback functions

    Example:
        >>> class MyService(BaseService):
        ...     def process_request(self, request):
        ...         return await self.agent.inference_async(request)
    """

    def __init__(
        self,
        agent_type: str,
        agent_config: dict,
    ):
        """
        Initialize the BaseService with an agent instance.

        Args:
            agent_type: String identifier for the agent type
            agent_config: Configuration dictionary for agent creation

        Raises:
            ValueError: If agent_type is not registered
            RuntimeError: If agent creation fails
        """
        self.agent_type = agent_type
        self.status_callbacks: List[StatusCallback] = []
        self.logger = get_logger(__name__, "service")

        # Create agent instance
        try:
            self.agent = AgentFactory.create_agent(
                agent_type=agent_type,
                **agent_config
            )
            self.logger.info(f"Service initialized with agent: {self.agent.name}")
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise

    def register_status_callback(self, callback: StatusCallback) -> None:
        """
        Register a status update callback.

        Multiple callbacks can be registered. When status updates occur,
        all registered callbacks will be invoked.

        Args:
            callback: Function to call with (status_type, message) arguments
        """
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
            self.logger.debug(f"Registered status callback: {callback.__name__}")

    def unregister_status_callback(self, callback: StatusCallback) -> None:
        """
        Unregister a previously registered status callback.

        Args:
            callback: The callback function to remove
        """
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
            self.logger.debug(f"Unregistered status callback: {callback.__name__}")

    def _notify_status(self, status_type: str, message: str) -> None:
        """
        Notify all registered callbacks of a status update.

        Args:
            status_type: Type of status (e.g., "processing", "summarizing", "clear")
            message: Status message content
        """
        for callback in self.status_callbacks:
            try:
                callback(status_type, message)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}", exc_info=True)

    @abstractmethod
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process an agent request (must be implemented by subclasses).

        This method should handle the complete request lifecycle including:
        - Pre-processing
        - Agent inference
        - Post-processing
        - Error handling

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse with status, answer, and metadata

        Raises:
            RuntimeError: If request processing fails
        """
        pass

    def get_agent_info(self) -> dict:
        """
        Get information about the managed agent.

        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.agent.name,
            "type": self.agent_type,
            "class": self.agent.__class__.__name__,
        }

    def __repr__(self) -> str:
        """String representation of the service."""
        return f"{self.__class__.__name__}(agent_type='{self.agent_type}', agent={self.agent})"
