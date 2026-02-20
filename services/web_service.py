"""
Async Web service implementation for real-time streaming.

This module provides a web service with streaming capabilities,
delivering real-time tool call updates and content generation.
"""

import asyncio
from typing import Optional, Dict, AsyncGenerator, Any
from services.base_service import BaseService
from core.schema import AgentRequest, AgentResponse
from core.logger import get_logger
from ui.tool_ui import ToolUIManager
from config.config_loader import Config


class WebService(BaseService):
    """
    Web backend service with real-time streaming capabilities.

    This service extends BaseService with streaming support for web UI:
    - Real-time tool call updates
    - Streamed content generation
    - Async generator interface
    - Session management for multi-user support

    Example:
        >>> service = WebService(
        ...     agent_type="mcp_async_agent",
        ...     agent_config={"model_name": "deepseek-chat"}
        ... )
        >>> async for event in service.process_request_stream(request):
        ...     print(event["type"], event["data"])
    """

    def __init__(self, agent_type: str, agent_config: dict):
        """
        Initialize the Web service.

        Args:
            agent_type: Type of agent to create (must be "mcp_async_agent")
            agent_config: Configuration dictionary for agent creation
        """
        super().__init__(agent_type, agent_config)
        self.logger = get_logger(__name__, "web_service")

        # Disable CLI UI for web environment
        ToolUIManager.disable()

        # Session management for multi-user support
        self._sessions: Dict[str, dict] = {}

        # Inject status callback
        if hasattr(self.agent, "status_callback"):

            def agent_status_bridge(status_type: str, message: str):
                self._notify_status(status_type, message)

            self.agent.status_callback = agent_status_bridge

    async def process_request(
        self, request: AgentRequest, session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Process an agent request asynchronously (backward compatible).

        This method collects all streaming events and returns a complete response.
        Use process_request_stream() for real-time updates.

        Args:
            request: AgentRequest containing prompt
            session_id: Optional session identifier

        Returns:
            AgentResponse with complete answer
        """
        # Collect events
        events = []
        async for event in self.process_request_stream(request, session_id):
            events.append(event)

        # Build response
        answer_parts = []
        tool_calls = []

        for event in events:
            if event["type"] == "content":
                answer_parts.append(event["data"])
            elif event["type"] == "tool_call_start":
                tool_calls.append(event["data"])

        return AgentResponse(
            status="success",
            answer="".join(answer_parts),
            metadata={"tool_calls": tool_calls},
        )

    async def process_request_stream(
        self, request: AgentRequest, session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream request processing with real-time updates.

        This method yields events as they happen from the agent.

        Args:
            request: AgentRequest containing prompt
            session_id: Optional session identifier

        Yields:
            Dict with event type and data
        """
        # Initialize session if needed
        if session_id:
            self._get_or_create_session(session_id)

        self._notify_status("processing", "Processing your request...")

        # Get backend timeout from config
        config = Config.get_instance()
        backend_timeout = config.get("mcp.connection.backend_timeout", 100)

        try:
            # Wrap agent streaming with timeout using a helper coroutine
            stream_generator = self._stream_from_agent(request, session_id)

            # Process events with timeout
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(
                        stream_generator.__anext__(),
                        timeout=backend_timeout
                    )
                    yield event
                except StopAsyncIteration:
                    # Stream ended naturally
                    break

            self._notify_status("completed", "Request completed successfully")

        except asyncio.TimeoutError:
            error_message = f"Request processing timeout after {backend_timeout} seconds"
            self.logger.error(error_message)
            self._notify_status("error", error_message)
            yield {"type": "error", "data": error_message}

        except Exception as e:
            error_message = f"Error processing request: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            self._notify_status("error", error_message)
            yield {"type": "error", "data": error_message}

    async def _stream_from_agent(
        self, request: AgentRequest, session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Internal method to stream from agent.

        Args:
            request: AgentRequest containing prompt
            session_id: Optional session identifier

        Yields:
            Dict with event type and data
        """
        # Use agent's streaming method
        async for event in self.agent.inference_stream(request):
            # Store in session
            if session_id and event["type"] in ["tool_call_start", "content"]:
                self._store_event(session_id, event)

            # Forward event
            yield event

    def _get_or_create_session(self, session_id: str) -> dict:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "created_at": None,
                "last_active": None,
            }
        return self._sessions[session_id]

    def _store_event(self, session_id: str, event: Dict[str, Any]) -> None:
        """Store event in session history."""
        session = self._get_or_create_session(session_id)
        session["messages"].append(event)

    def get_session_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        session = self._get_or_create_session(session_id)
        return session.get("messages", [])

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._sessions:
            self._sessions[session_id]["messages"] = []
        self.logger.info(f"Cleared session: {session_id}")

        if hasattr(self.agent, "clear_history"):
            self.agent.clear_history()

    def clear_agent_history(self) -> None:
        """Clear the agent's conversation history."""
        if hasattr(self.agent, "clear_history"):
            self.agent.clear_history()
            self.logger.info("Agent history cleared")
            self._notify_status("info", "Conversation history cleared")

    def get_available_tools(self) -> list:
        """Get list of available tools from the agent."""
        if hasattr(self.agent, "list_tools"):
            try:
                tools = self.agent.list_tools()
                return tools
            except Exception as e:
                self.logger.error(f"Failed to list tools: {e}", exc_info=True)
                return []
        return []
