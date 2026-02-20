"""
IntelliSearch Agents Module

This module provides agent implementations for various search and reasoning tasks.
All agents inherit from BaseAgent and follow a unified interface.
"""

from agents.mcp_agent import MCPBaseAgent
from agents.mcp_agent_async import MCPAsyncAgent

__all__ = [
    "MCPBaseAgent",
    "MCPAsyncAgent"
]
