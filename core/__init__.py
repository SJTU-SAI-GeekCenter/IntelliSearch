"""
IntelliSearch Core Module

This module provides the core abstractions and utilities for the agent system,
including base classes, data schemas, and factory patterns.
"""

from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from core.factory import AgentFactory

__all__ = [
    "BaseAgent",
    "AgentRequest",
    "AgentResponse",
    "AgentFactory",
]
