"""
Async MCP-based Agent implementation for real-time streaming.

This module provides an async agent with streaming capabilities for web UI,
delivering real-time tool call updates and content generation.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from openai import OpenAI
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from tools.mcp_base import MCPBase
from memory.sequential import SequentialMemory
from core.logger import get_logger
from config.config_loader import Config


# Type alias for status callback function
StatusCallback = Optional[callable]


class MCPAsyncAgent(BaseAgent):
    """
    Async MCP-enhanced Agent with real-time streaming capabilities.

    This agent extends MCPBaseAgent with streaming output for web UI:
    - Real-time tool call updates
    - Streamed content generation
    - Async generator interface
    - Backward compatible with synchronous inference

    The agent uses:
    - An MCPBase component for tool communication
    - A SequentialMemory for conversation history
    - Async generators for streaming output

    Attributes:
        name: Agent identifier
        model_name: LLM model to use
        system_prompt: System prompt for the LLM
        max_tool_call: Maximum tool calls per query
        client: OpenAI-compatible API client
        mcp_base: MCPBase component for tool communication
        memory: SequentialMemory for conversation management
        logger: Logger instance

    Example:
        >>> agent = MCPAsyncAgent(
        ...     name="AsyncAgent",
        ...     model_name="deepseek-chat",
        ...     server_config_path="./config/config.yaml"
        ... )
        >>> async for event in agent.inference_stream(request):
        ...     print(event["type"], event["data"])
    """

    def __init__(
        self,
        name: str = "MCPAsyncAgent",
        model_name: str = "deepseek-chat",
        system_prompt: str = "You are a helpful assistant",
        server_config_path: str = "config/config.yaml",
        max_tool_call: int = 5,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        status_callback: StatusCallback = None,  # type: ignore
    ):
        """
        Initialize the MCPAsyncAgent.

        Args:
            name: Agent identifier
            model_name: LLM model name
            system_prompt: System prompt for LLM
            server_config_path: Path to MCP server configuration
            max_tool_call: Maximum tool calls allowed per query
            base_url: Optional base URL for LLM API
            api_key: Optional API key
            status_callback: Optional callback for status updates
        """
        super().__init__(name=name)

        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_tool_call = int(max_tool_call)
        self.status_callback = status_callback

        # Initialize memory component
        self.memory = SequentialMemory(system_prompt=system_prompt)

        # Setup result directory
        self.time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Initialize LLM client
        self.base_url = base_url or os.environ.get("BASE_URL")
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not found. Please set OPENAI_API_KEY environment variable."
            )

        self.client: OpenAI = OpenAI(api_key=api_key, base_url=self.base_url)

        # Initialize MCP communication component
        self.mcp_base = MCPBase(config_path=server_config_path)
        self.available_tools = []

        # Setup logger
        self.logger = get_logger(__name__, "async_agent")
        self.logger.info(f"{self.name} initialized with model: {self.model_name}")

    def _notify_status(self, status_type: str, message: str) -> None:
        """Notify status changes to registered callback."""
        if self.status_callback:
            self.status_callback(status_type, message)

    def inference(self, request: AgentRequest) -> AgentResponse:
        """
        Synchronous inference for backward compatibility.

        This method collects all streaming events and returns a complete response.
        Use inference_stream() for real-time updates.

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse with complete answer and metadata
        """
        # Try to get running event loop, or create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            # Collect all events
            events = []
            loop.run_until_complete(self._collect_events(request, events))

            # Build response from events
            return self._build_response_from_events(events, request)

        finally:
            # Only close if we created the loop
            if loop.is_closed():
                pass
            elif asyncio.get_event_loop() is not loop:
                loop.close()

    async def _collect_events(
        self, request: AgentRequest, events: List[Dict[str, Any]]
    ) -> None:
        """Collect all streaming events into a list."""
        async for event in self.inference_stream(request):
            events.append(event)

    def _build_response_from_events(
        self, events: List[Dict[str, Any]], request: AgentRequest
    ) -> AgentResponse:
        """Build AgentResponse from collected events."""
        answer_parts = []
        tools_used = []
        tool_calls_details = []

        for event in events:
            if event["type"] == "content":
                answer_parts.append(event["data"])
            elif event["type"] == "tool_call_start":
                tool_data = event["data"]
                tools_used.append(tool_data["name"])
                tool_calls_details.append(tool_data)

        return AgentResponse(
            status="success",
            answer="".join(answer_parts),
            metadata={
                "model_name": self.model_name,
                "tools_called": tools_used,
                "tool_calls": tool_calls_details,
                "iterations": len(tools_used),
                "tokens_used": {},
            },
        )

    async def inference_stream(
        self, request: AgentRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream inference with real-time updates.

        This method yields events as they happen:
        - Tool call start: When a tool is invoked
        - Tool result: When a tool completes
        - Content: As response text is generated
        - Done: When complete
        - Error: If an error occurs

        Args:
            request: AgentRequest containing prompt and metadata

        Yields:
            Dict with keys:
                - type: "tool_call_start" | "tool_result" | "content" | "done" | "error"
                - data: Event-specific data
        """
        max_iterations = request.metadata.get("max_iterations", self.max_tool_call)

        try:
            self._notify_status("processing", "Starting request processing...")

            # Discover available tools (returns a Dict)
            available_tools_dict = await self.mcp_base.list_tools()

            # Store for later use
            self.available_tools = available_tools_dict
            self.logger.info(f"Available tools nums: {len(list(available_tools_dict.keys()))}")
            self.logger.info(f"Available tools: {list(available_tools_dict.keys())}")

            tools = self._format_tools_for_llm(available_tools_dict)

            # Add user message to memory
            user_message = request.prompt
            self.memory.add({"role": "user", "content": user_message})

            tools_used = []

            for round_count in range(max_iterations):
                self.logger.info(f"Processing round {round_count + 1}/{max_iterations}")

                # Get current messages from memory
                messages = self.memory.get_view("chat_messages")

                # Get LLM timeout from config
                config = Config.get_instance()
                llm_timeout = config.get("mcp.connection.llm_timeout", 90)

                # LLM completion with timeout
                completion = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model_name,
                        messages=messages,
                        tools=tools
                    ),
                    timeout=llm_timeout
                )

                # Check for tool calls
                tool_call_lists = completion.choices[0].message.tool_calls
                has_tool_calls = (
                    tool_call_lists is not None and len(tool_call_lists) > 0
                )

                if has_tool_calls:
                    # Add assistant message to memory
                    self.memory.add(completion.choices[0].message.model_dump())

                    # Execute tool calls
                    try:
                        tool_results = await self.mcp_base.execute_tool_calls(
                            tool_call_lists, self.available_tools
                        )

                        # Yield tool call events in real-time
                        for tool_detail in tool_results.get("tools_detailed", []):
                            # Tool call start event
                            yield {"type": "tool_call_start", "data": tool_detail}

                            self._notify_status(
                                "tool", f"Tool completed: {tool_detail['name']}"
                            )

                            # Tool result event
                            yield {"type": "tool_result", "data": tool_detail}

                        tools_used.extend(tool_results["tools_used"])

                        # Store detailed tool information for web UI
                        if "tools_detailed" in tool_results:
                            if not hasattr(self, "_tools_detailed"):
                                self._tools_detailed = []
                            self._tools_detailed.extend(tool_results["tools_detailed"])

                        self.memory.add_many(tool_results["history"])
                        continue

                    except Exception as tool_exc:
                        error_text = str(tool_exc)
                        if (
                            "Access Denied" in error_text
                            or "denied" in error_text.lower()
                        ):
                            # Rollback on permission denied
                            if (
                                hasattr(self.memory, "entries")
                                and self.memory.entries
                                and self.memory.entries[-1].get("role") == "assistant"
                            ):
                                self.memory.entries.pop()
                        raise

                else:
                    # No tool calls, generate final response
                    self._notify_status("summarizing", "Generating final response...")

                    final_answer = completion.choices[0].message.content
                    self.memory.add({"role": "assistant", "content": final_answer})

                    # Stream the content in chunks
                    chunk_size = 20
                    for i in range(0, len(final_answer), chunk_size):
                        chunk = final_answer[i : i + chunk_size]
                        yield {"type": "content", "data": chunk}

                    self._notify_status("clear", "")
                    yield {"type": "done"}
                    return

            # Max iterations reached
            self.logger.info(f"Max tool call limit reached: {max_iterations}")
            self._notify_status(
                "warning",
                f"Reached maximum tool call limit, generating final response...",
            )

            # Generate final response
            final_answer = await self._generate_final_response()

            # Stream the content
            chunk_size = 20
            for i in range(0, len(final_answer), chunk_size):
                chunk = final_answer[i : i + chunk_size]
                yield {"type": "content", "data": chunk}

            self._notify_status("clear", "")
            yield {"type": "done"}

        except Exception as e:
            error_text = str(e)
            if "Access Denied" not in error_text and "denied" not in error_text.lower():
                self.logger.error(f"Inference error: {e}", exc_info=True)

            yield {"type": "error", "data": error_text}

    def _format_tools_for_llm(self, tools: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format tools for LLM consumption."""
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "input_schema": tool.get("input_schema"),
                },
            }
            for tool in list(tools.values())
        ]
        return available_tools

    async def _generate_final_response(self) -> str:
        """Generate final response after max iterations."""
        messages = self.memory.get_view("chat_messages")

        # Get LLM timeout from config
        config = Config.get_instance()
        llm_timeout = config.get("mcp.connection.llm_timeout", 90)

        # LLM completion with timeout
        completion = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=messages
            ),
            timeout=llm_timeout
        )

        final_answer = completion.choices[0].message.content
        self.memory.add({"role": "assistant", "content": final_answer})

        return final_answer

    def clear_history(self) -> None:
        """Clear conversation history."""
        if hasattr(self.memory, "clear"):
            self.memory.clear()
        self.logger.info("Conversation history cleared")

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        if isinstance(self.available_tools, dict):
            return list(self.available_tools.values())
        elif isinstance(self.available_tools, list):
            return self.available_tools
        return []

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if isinstance(self.available_tools, dict):
            return self.available_tools.get(tool_name)
        elif isinstance(self.available_tools, list):
            for tool_info in self.available_tools:
                if isinstance(tool_info, dict) and tool_info.get("name") == tool_name:
                    return tool_info
        return None
