"""
Async Web backend implementation for real-time streaming.

This module provides the async web API backend with true streaming,
delivering real-time tool call updates and content generation.
"""

import json
import uvicorn
from typing import Optional, AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.web_service import WebService
from core.schema import AgentRequest
from core.logger import get_logger


class ChatRequest(BaseModel):
    """Chat request model for API."""

    message: str
    session_id: Optional[str] = None
    use_tools: bool = True


class AsyncWebBackend:
    """
    Async Web backend with real-time streaming capabilities.

    This backend delivers true streaming:
    - Tool calls appear immediately when executed
    - Content is streamed in real-time
    - No waiting for complete execution

    Attributes:
        service: The WebService instance
        app: FastAPI application instance
        host: Server host address
        port: Server port

    Example:
        >>> backend = AsyncWebBackend(
        ...     agent_type="mcp_async_agent",
        ...     agent_config={"model_name": "deepseek-chat"},
        ...     host="0.0.0.0",
        ...     port=8001
        ... )
        >>> backend.run()
    """

    def __init__(
        self,
        agent_type: str,
        agent_config: dict,
        host: str = "0.0.0.0",
        port: int = 8001,
    ):
        """
        Initialize the Async Web backend.

        Args:
            agent_type: Type of agent to create (must be "mcp_async_agent")
            agent_config: Configuration for agent creation
            host: Server host address
            port: Server port
        """
        self.logger = get_logger(__name__, "async_web_backend")
        self.host = host
        self.port = port

        # Initialize service
        self.service = WebService(agent_type, agent_config)

        # Setup FastAPI app
        self.app = FastAPI(
            title="IntelliSearch API (Async)",
            description="Intelligent search with real-time streaming",
            version="3.2.0",
        )

        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register routes
        self._setup_routes()

        self.logger.info("Async Web backend initialized")

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "IntelliSearch Async Web API",
                "version": "3.2.0",
                "streaming": "real-time",
            }

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            agent_info = {
                "name": self.service.agent.name,
                "type": type(self.service.agent).__name__,
            }
            return {"status": "healthy", "agent": agent_info}

        @self.app.post("/api/chat/stream")
        async def chat_stream(request: ChatRequest):
            """
            Real-time streaming chat endpoint.

            This endpoint delivers true streaming:
            - Tool calls appear immediately when executed
            - Content is streamed in real-time
            """
            return StreamingResponse(
                self._generate_real_stream(
                    request.message, request.session_id, request.use_tools
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        @self.app.get("/api/chat/tools")
        async def get_tools():
            """Get available tools."""
            tools = self.service.get_available_tools()
            return {"tools": tools}

        @self.app.post("/api/chat/clear")
        async def clear_chat(request: ChatRequest):
            """Clear chat session."""
            if request.session_id:
                self.service.clear_session(request.session_id)
            return {"status": "cleared"}

    async def _generate_real_stream(
        self, message: str, session_id: Optional[str], use_tools: bool
    ) -> AsyncGenerator[str, None]:
        """
        Generate real-time streaming response.

        This method streams events as they happen from the agent:
        1. Tool call start → Immediately sent
        2. Tool result → Immediately sent
        3. Content chunk → Streamed in real-time

        Args:
            message: User message
            session_id: Optional session identifier
            use_tools: Whether to use tools

        Yields:
            Server-Sent Events (SSE) formatted strings
        """
        try:
            # Create request
            request = AgentRequest(prompt=message)

            # Stream from service
            async for event in self.service.process_request_stream(request, session_id):
                # Map event types to SSE format
                if event["type"] == "tool_call_start":
                    tool_data = event["data"]
                    sse_event = {
                        "type": "tool_call_start",
                        "tool_call": {
                            "name": tool_data.get("name", "unknown"),
                            "arguments": tool_data.get("arguments", {}),
                            "result": "",  # Will be in tool_result
                            "success": tool_data.get("success", True),
                        },
                    }
                    yield f"data: {json.dumps(sse_event)}\n\n"

                elif event["type"] == "tool_result":
                    tool_data = event["data"]
                    sse_event = {
                        "type": "tool_result",
                        "tool_call": {
                            "name": tool_data.get("name", "unknown"),
                            "arguments": tool_data.get("arguments", {}),
                            "result": tool_data.get("result", ""),
                            "success": tool_data.get("success", True),
                        },
                    }
                    yield f"data: {json.dumps(sse_event)}\n\n"

                elif event["type"] == "content":
                    content_event = {"type": "content", "content": event["data"]}
                    yield f"data: {json.dumps(content_event)}\n\n"

                elif event["type"] == "error":
                    error_event = {"type": "error", "error": event["data"]}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                elif event["type"] == "done":
                    yield "data: [DONE]\n\n"
                    return

        except Exception as e:
            self.logger.error(f"Stream generation error: {e}", exc_info=True)
            error_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
            yield "data: [DONE]\n\n"

    def run(self):
        """Run the async web server."""
        try:
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.logger.error(f"Web server error: {e}", exc_info=True)
            raise


def create_async_web_backend(
    agent_type: str, agent_config: dict, host: str = "0.0.0.0", port: int = 8001
) -> AsyncWebBackend:
    """
    Factory function to create an AsyncWebBackend instance.

    Args:
        agent_type: Type of agent to create
        agent_config: Configuration for agent creation
        host: Server host address
        port: Server port

    Returns:
        Configured AsyncWebBackend instance
    """
    return AsyncWebBackend(
        agent_type=agent_type, agent_config=agent_config, host=host, port=port
    )
