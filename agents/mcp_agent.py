"""
MCP-based Agent implementation for IntelliSearch.

This module provides an agent that leverages Model Context Protocol (MCP) tools
to enhance search and retrieval capabilities with multi-step reasoning.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from tools.mcp_base import MCPBase
from ui.status_manager import get_status_manager
from memory.sequential import SequentialMemory
from core.logger import get_logger


class MCPBaseAgent(BaseAgent):
    """
    MCP-enhanced Agent with multi-turn conversation and tool calling capabilities.

    This agent integrates with MCP servers to provide enhanced search and data
    retrieval capabilities. It supports multi-round reasoning with automatic tool
    selection and execution.

    The agent uses:
    - An MCPBase component for all MCP communication operations
    - A SequentialMemory component for conversation history management

    Attributes:
        name: Agent identifier (inherited from BaseAgent)
        model_name: LLM model to use for inference
        system_prompt: System prompt for the LLM
        max_tool_call: Maximum number of tool calls per query
        client: OpenAI-compatible API client
        mcp_base: MCPBase component for tool communication
        memory: SequentialMemory for conversation management
        logger: Logger instance

    Example:
        >>> agent = MCPBaseAgent(
        ...     name="SearchAgent",
        ...     model_name="glm-4.5",
        ...     server_config_path="./config.json"
        ... )
        >>> request = AgentRequest(prompt="Find recent AI papers")
        >>> response = agent.inference(request)
        >>> print(response.answer)
    """

    def __init__(
        self,
        name: str = "MCPBaseAgent",
        model_name: str = "deepseek-chat",
        system_prompt: str = "You are a helpful assistant",
        server_config_path: str = "config/config.yaml",
        max_tool_call: int = 5,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the MCPBaseAgent.

        Args:
            name: Agent identifier
            model_name: LLM model name (default: "glm-4.5")
            system_prompt: System prompt for LLM
            server_config_path: Path to MCP server configuration file
            max_tool_call: Maximum tool calls allowed per query
            base_url: Optional base URL for LLM API (default: from env BASE_URL)
            api_key: Optional API key (default: from env OPENAI_API_KEY)

        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(name=name)

        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_tool_call = int(max_tool_call)

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
        self.logger = get_logger(__name__)
        self.logger.info(f"{self.name} initialized with model: {self.model_name}")

    def inference(self, request: AgentRequest) -> AgentResponse:
        """
        Execute agent inference with MCP tool enhancement.

        This method processes the user prompt through the LLM with access to
        MCP tools. It handles multi-turn reasoning, tool calling, and response
        generation according to the configured parameters.

        Args:
            request: AgentRequest containing prompt and optional metadata

        Returns:
            AgentResponse with status, generated answer, and execution metadata

        Raises:
            RuntimeError: If inference execution fails
        """
        # Extract configuration from metadata
        max_iterations = request.metadata.get("max_iterations", self.max_tool_call)

        try:
            # Run async processing
            result = asyncio.run(
                self._process_query_async(
                    user_message=request.prompt,
                    max_iterations=max_iterations,
                )
            )

            # Build response metadata
            response_metadata = {
                "model_name": self.model_name,
                "iterations_used": result.get("iterations", 0),
                "tools_called": result.get("tools_called", []),
                "tokens_used": result.get("tokens", {}),
            }

            return AgentResponse(
                status="success",
                answer=result.get("answer", ""),
                metadata=response_metadata,
            )

        except Exception as e:
            error_text = str(e)
            if "Access Denied" in error_text or "denied" in error_text.lower():
                return AgentResponse(
                    status="failed",
                    answer=error_text,
                    metadata={"error": error_text, "error_type": type(e).__name__},
                )

            self.logger.error(f"Inference failed: {e}", exc_info=True)
            return AgentResponse(
                status="failed",
                answer=f"Error during inference: {error_text}",
                metadata={"error": error_text, "error_type": type(e).__name__},
            )

    async def _process_query_async(
        self, user_message: str, max_iterations: int
    ) -> Dict[str, Any]:
        """
        Process user query asynchronously with MCP tool support.

        Args:
            user_message: User input query
            max_iterations: Maximum tool call iterations

        Returns:
            Dictionary containing answer and metadata
        """
        # Discover available tools using MCPBase component
        tools = await self.mcp_base.list_tools()
        self.logger.info(f"Available tools nums: {len(list(tools.keys()))}")
        self.logger.info(f"Available tools: {list(tools.keys())}")
        self.tools_store = tools

        # Format tools for LLM (OpenAI Format)
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

        # Add user message to memory
        self.memory.add({"role": "user", "content": user_message})

        tools_called = []
        final_answer = ""

        try:
            for round_count in range(max_iterations):
                self.logger.info(f"Processing round {round_count + 1}/{max_iterations}")

                # Get current messages from memory
                messages = self.memory.get_view("chat_messages")

                # Get LLM response
                completion = self.client.chat.completions.create(
                    model=self.model_name, messages=messages, tools=available_tools
                )

                tool_call_lists = completion.choices[0].message.tool_calls
                has_tool_calls = (
                    tool_call_lists is not None and len(tool_call_lists) > 0
                )

                # Check for tool calls
                if has_tool_calls:
                    # Add assistant message to memory
                    self.memory.add(completion.choices[0].message.model_dump())

                    # Execute tool calls using MCPBase component
                    try:
                        tool_results = await self.mcp_base.execute_tool_calls(
                            tool_call_lists, tools
                        )
                    except Exception as tool_exc:
                        # If permission was denied, rollback the last assistant tool-call message
                        error_text = str(tool_exc)
                        if (
                            "Access Denied" in error_text
                            or "denied" in error_text.lower()
                        ):
                            if (
                                hasattr(self.memory, "entries")
                                and self.memory.entries
                                and self.memory.entries[-1].get("role") == "assistant"
                            ):
                                self.memory.entries.pop()
                        raise

                    tools_called.extend(tool_results["tools_used"])
                    self.memory.add_many(tool_results["history"])
                    continue

                else:
                    # LLM completed without tool calls - show SUMMARIZING status

                    status_mgr = get_status_manager()
                    status_mgr.set_summarizing("Generating final response...")

                    final_answer = completion.choices[0].message.content
                    self.memory.add({"role": "assistant", "content": final_answer})

                    status_mgr.clear()

                    return {
                        "answer": final_answer,
                        "iterations": round_count + 1,
                        "tools_called": tools_called,
                        "tokens": {},
                    }

            # Max iterations reached
            self.logger.warning(f"Max tool call limit reached: {max_iterations}")
            final_answer = await self._generate_final_response()

            return {
                "answer": final_answer,
                "iterations": max_iterations,
                "tools_called": tools_called,
                "tokens": {},
            }

        except Exception as e:
            error_text = str(e)
            if "Access Denied" in error_text or "denied" in error_text.lower():
                raise e

            error_message = f"Error during query processing: {e}"
            self.logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message)

    async def _generate_final_response(self) -> str:
        """
        Generate final response after max iterations reached.

        Args:
            available_tools: List of available tools (empty to force final response)

        Returns:
            Final text response from LLM
        """
        # Show SUMMARIZING status

        status_mgr = get_status_manager()
        status_mgr.set_summarizing("Synthesizing gathered information...")

        self.memory.add(
            {
                "role": "user",
                "content": (
                    "You have reached the maximum tool call limit. "
                    "Please use the information gathered so far to generate your final answer."
                ),
            }
        )

        messages = self.memory.get_view("chat_messages")
        completion = self.client.chat.completions.create(
            model=self.model_name, messages=messages
        )
        final_content = completion.choices[0].message.content
        self.memory.add({"role": "assistant", "content": final_content})

        status_mgr.clear()

        return final_content

    def export_conversation(self, output_file_path: Optional[str] = None) -> str:
        """
        Export conversation history to JSON file.

        Args:
            output_file_path: Optional custom output path

        Returns:
            Path to the exported file
        """
        if not output_file_path:
            output_file_path = os.path.join(
                self.result_dir, f"{self.time_stamp}_memory.json"
            )

        dir_path, _ = os.path.split(output_file_path)
        os.makedirs(dir_path, exist_ok=True)

        # Export from memory
        memory_data = self.memory.export()
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(memory_data)

        self.logger.info(f"Conversation exported to {output_file_path}")
        return output_file_path

    def append_history(
        self, history_episodes: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Append conversation episodes to memory.

        Args:
            history_episodes: List of history dictionaries with 'role' and 'content'
        """
        self.memory.append_history(history_episodes)

    def clear_history(self) -> None:
        """Clear conversation memory, keeping system prompt."""
        self.memory.clear_history()

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"model='{self.model_name}', "
            f"max_tools={self.max_tool_call}"
            f")"
        )
