"""
Agent Factory for creating agent instances.

This module implements the Factory pattern to decouple agent creation
from business logic, making it easy to add new agent types without
modifying existing code.
"""

from typing import Dict, Type
from core.base import BaseAgent


class AgentFactory:
    """
    Factory class for creating agent instances.

    This factory centralizes agent creation logic and provides a simple
    interface for instantiating different agent types based on configuration.

    Attributes:
        _agents: Registry mapping agent type identifiers to their classes

    Example:
        >>> factory = AgentFactory()
        >>> agent = factory.create_agent(
        ...     agent_type="mcp_base_agent",
        ...     name="MyAgent",
        ...     model_name="glm-4.5"
        ... )
        >>> response = agent.inference(request)
    """

    _agents: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def _ensure_default_agents(cls) -> None:
        """
        Ensure default agents are registered.

        This method is called lazily to avoid circular imports.
        """
        if "mcp_base_agent" not in cls._agents:
            from agents.mcp_agent import MCPBaseAgent

            cls._agents["mcp_base_agent"] = MCPBaseAgent

    @classmethod
    def register_agent(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register a new agent type with the factory.

        This method allows for dynamic registration of new agent types
        at runtime, enabling plugins and extensions.

        Args:
            agent_type: String identifier for the agent type
            agent_class: Class that inherits from BaseAgent

        Raises:
            TypeError: If agent_class does not inherit from BaseAgent
            ValueError: If agent_type is already registered

        Example:
            >>> class MyCustomAgent(BaseAgent):
            ...     def inference(self, request):
            ...         return AgentResponse(status="success", answer="...", metadata={})
            >>>
            >>> AgentFactory.register_agent("custom", MyCustomAgent)
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(
                f"Agent class must inherit from BaseAgent, "
                f"got {type(agent_class).__name__}"
            )

        if agent_type in cls._agents:
            raise ValueError(
                f"Agent type '{agent_type}' is already registered. "
                f"Use a different name or unregister it first."
            )

        cls._agents[agent_type] = agent_class

    @classmethod
    def unregister_agent(cls, agent_type: str) -> None:
        """
        Unregister an agent type from the factory.

        Args:
            agent_type: String identifier of the agent to unregister

        Raises:
            KeyError: If agent_type is not registered
        """
        if agent_type not in cls._agents:
            raise KeyError(f"Agent type '{agent_type}' is not registered")

        del cls._agents[agent_type]

    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> BaseAgent:
        """
        Create an agent instance based on type.

        This method instantiates an agent of the specified type with
        the provided configuration parameters.

        Args:
            agent_type: String identifier for the agent type
            **kwargs: Configuration parameters passed to the agent's __init__

        Returns:
            Instance of the requested agent type

        Raises:
            ValueError: If agent_type is not registered

        Example:
            >>> agent = AgentFactory.create_agent(
            ...     agent_type="mcp_base_agent",
            ...     name="SearchAgent",
            ...     model_name="deepseek-chat",
            ...     max_tool_call=10
            ... )
        """
        # Ensure default agents are registered
        cls._ensure_default_agents()

        agent_class = cls._agents.get(agent_type)

        if not agent_class:
            available_types = ", ".join(cls._agents.keys())
            raise ValueError(
                f"Unknown agent type: '{agent_type}'. "
                f"Available types: {available_types}"
            )

        try:
            agent_instance = agent_class(**kwargs)
            return agent_instance
        except Exception as e:
            raise RuntimeError(
                f"Failed to create agent of type '{agent_type}': {e}"
            ) from e

    @classmethod
    def list_agent_types(cls) -> list[str]:
        """
        List all registered agent types.

        Returns:
            List of registered agent type identifiers

        Example:
            >>> types = AgentFactory.list_agent_types()
            >>> print(types)
            ['mcp_base_agent']
        """
        # Ensure default agents are registered
        cls._ensure_default_agents()
        return list(cls._agents.keys())

    @classmethod
    def is_registered(cls, agent_type: str) -> bool:
        """
        Check if an agent type is registered.

        Args:
            agent_type: String identifier to check

        Returns:
            True if agent_type is registered, False otherwise
        """
        # Ensure default agents are registered
        cls._ensure_default_agents()
        return agent_type in cls._agents
