"""
CLI-specific service implementation for IntelliSearch.

This module provides a service implementation optimized for CLI interactions,
handling request processing with status updates suitable for terminal UI.
"""

import asyncio
from typing import Optional
from services.base_service import BaseService
from core.schema import AgentRequest, AgentResponse
from core.logger import get_logger


class CLIService(BaseService):
    """
    CLI backend service for managing agent interactions in a terminal environment.

    This service extends BaseService with CLI-specific behavior including:
    - Synchronous wrapper around async agent operations
    - Status notification integration
    - CLI-focused error handling

    Example:
        >>> service = CLIService(
        ...     agent_type="mcp_base_agent",
        ...     agent_config={"name": "CLI_Agent", "model_name": "deepseek-chat"}
        ... )
        >>> response = await service.process_request(
        ...     AgentRequest(prompt="Search for AI papers")
        ... )
    """

    def __init__(self, agent_type: str, agent_config: dict):
        """
        Initialize the CLI service.

        Args:
            agent_type: String identifier for the agent type
            agent_config: Configuration dictionary for agent creation
        """
        super().__init__(agent_type, agent_config)
        self.logger = get_logger(__name__, "cli_service")

        # Inject our status callback into the agent if it supports it
        if hasattr(self.agent, 'status_callback'):
            # Set up a bridge: service callbacks -> agent callback
            def agent_status_bridge(status_type: str, message: str):
                """Bridge from agent to service status notifications."""
                self._notify_status(status_type, message)

            self.agent.status_callback = agent_status_bridge
            self.logger.debug("Status callback bridge established with agent")

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process an agent request asynchronously.

        This method handles the complete request lifecycle:
        1. Notifies processing status
        2. Executes agent inference
        3. Handles errors gracefully
        4. Returns structured response

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse with status, answer, and metadata

        Raises:
            RuntimeError: If agent inference fails critically
        """
        self._notify_status("processing", "Processing your request...")

        try:
            response = self.agent.inference(request)

            if response.status == "success":
                self._notify_status("completed", "Request completed successfully")
            else:
                self._notify_status("failed", f"Request failed: {response.answer}")

            return response

        except Exception as e:
            error_message = f"Error processing request: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            self._notify_status("error", error_message)

            return AgentResponse(
                status="failed",
                answer=error_message,
                metadata={"error": str(e), "error_type": type(e).__name__}
            )

    def process_request_sync(self, request: AgentRequest) -> AgentResponse:
        """
        Synchronous wrapper for process_request.

        This method allows the async process_request to be called from
        synchronous code (useful for CLI integration).

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse with status, answer, and metadata
        """
        return asyncio.run(self.process_request(request))

    def clear_agent_history(self) -> None:
        """Clear the agent's conversation history if supported."""
        if hasattr(self.agent, 'clear_history'):
            self.agent.clear_history()
            self.logger.info("Agent history cleared")
            self._notify_status("info", "Conversation history cleared")

    def export_conversation(self, output_path: Optional[str] = None) -> str:
        """
        Export agent conversation if supported.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to the exported file

        Raises:
            RuntimeError: If export fails or agent doesn't support export
        """
        if not hasattr(self.agent, 'export_conversation'):
            raise RuntimeError("Agent does not support conversation export")

        try:
            result_path = self.agent.export_conversation(output_path)
            self.logger.info(f"Conversation exported to {result_path}")
            self._notify_status("info", f"Conversation exported to {result_path}")
            return result_path
        except Exception as e:
            self.logger.error(f"Export failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to export conversation: {e}")

    def update_agent_config(self, **kwargs) -> None:
        """
        Update agent configuration at runtime.

        This allows dynamic configuration changes like model name, max tools, etc.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.agent, key):
                setattr(self.agent, key, value)
                self.logger.info(f"Agent config updated: {key} = {value}")
                self._notify_status("info", f"Configuration updated: {key}")
            else:
                self.logger.warning(f"Attempted to set non-existent attribute: {key}")
