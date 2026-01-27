"""
MCP-based Agent implementation for IntelliSearch.

This module provides an agent that leverages Model Context Protocol (MCP) tools
to enhance search and retrieval capabilities with multi-step reasoning.
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from ui.tool_ui import tool_ui

from openai import OpenAI
from mcp_module.server_manager import MultiServerManager
from mcp.types import CallToolResult
from backend.tool_hash import fix_tool_args

from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse


class MCPBaseAgent(BaseAgent):
    """
    MCP-enhanced Agent with multi-turn conversation and tool calling capabilities.

    This agent integrates with MCP servers to provide enhanced search and data
    retrieval capabilities. It supports multi-round reasoning with automatic tool
    selection and execution.

    Attributes:
        name: Agent identifier (inherited from BaseAgent)
        model_name: LLM model to use for inference
        system_prompt: System prompt for the LLM
        max_tool_call: Maximum number of tool calls per query
        client: OpenAI-compatible API client
        server_manager: MCP server connection manager
        history: Conversation history
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
        model_name: str = "glm-4.5",
        system_prompt: str = "You are a helpful assistant",
        server_config_path: str = "config/config.json",
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
        self.history: List[Dict[str, Any]] = []

        # Initialize conversation history with system prompt
        self.history.append({"role": "system", "content": system_prompt})

        # Setup result directory
        self.time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.result_dir = "./results"
        os.makedirs(self.result_dir, exist_ok=True)

        # Initialize LLM client
        self.base_url = base_url or os.environ.get("BASE_URL")
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not found. Please set OPENAI_API_KEY environment variable."
            )

        self.client: OpenAI = OpenAI(api_key=api_key, base_url=self.base_url)

        # Initialize MCP server manager
        self.config_path = server_config_path
        self.config = self._load_server_configs(config_path=server_config_path)
        self.server_manager = MultiServerManager(server_configs=self.config)
        self.available_tools = []

        # Setup logger
        self.logger = logging.getLogger(__name__)
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
            self.logger.error(f"Inference failed: {e}", exc_info=True)
            return AgentResponse(
                status="failed",
                answer=f"Error during inference: {str(e)}",
                metadata={"error": str(e), "error_type": type(e).__name__},
            )

    async def _process_query_async(
        self, user_message: str, max_iterations: int
    ) -> Dict[str, Any]:
        """
        Process user query asynchronously with MCP tool support.

        Args:
            user_message: User input query
            max_iterations: Maximum tool call iterations
            stream: Whether to use streaming output

        Returns:
            Dictionary containing answer and metadata
        """
        # Discover available tools
        tools = await self._list_tools()
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

        # Add user message to history
        self.history.append({"role": "user", "content": user_message})

        tools_called = []
        final_answer = ""

        try:
            for round_count in range(max_iterations):
                self.logger.info(f"Processing round {round_count + 1}/{max_iterations}")

                # Get LLM response
                completion = self.client.chat.completions.create(
                    model=self.model_name, messages=self.history, tools=available_tools
                )

                tool_call_lists = completion.choices[0].message.tool_calls
                has_tool_calls = (
                    tool_call_lists is not None and len(tool_call_lists) > 0
                )

                # Check for tool calls
                if has_tool_calls:
                    # Add assistant message to history
                    self.history.append(completion.choices[0].message.model_dump())

                    # Execute tool calls
                    tool_results = await self._execute_tool_calls(
                        tool_call_lists, tools
                    )

                    tools_called.extend(tool_results["tools_used"])
                    self.history.extend(tool_results["history"])
                    continue

                else:
                    # LLM completed without tool calls - show SUMMARIZING status
                    from ui.status_manager import get_status_manager
                    status_mgr = get_status_manager()
                    status_mgr.set_summarizing("Generating final response...")

                    final_answer = completion.choices[0].message.content
                    self.history.append({"role": "assistant", "content": final_answer})

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
            error_message = f"Error during query processing: {e}"
            self.logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message)

    async def _list_tools(self) -> Dict[str, Any]:
        """
        Discover and list all available MCP tools.

        Returns:
            Dictionary mapping tool names to their configurations
        """
        try:
            self.logger.info("Discovering MCP tools...")
            all_tools = await self.server_manager.connect_all_servers()

            # Save tools list for debugging
            tools_file = f"./results/{self.time_stamp}_list_tools.json"
            with open(tools_file, "w", encoding="utf-8") as f:
                json.dump(all_tools, f, indent=4, ensure_ascii=False)

            if not all_tools:
                raise RuntimeError("No MCP tools discovered")

            return all_tools

        except Exception as e:
            self.logger.error(f"Failed to discover tools: {e}")
            return {}
        finally:
            await self.server_manager.close_all_connections()

    async def _execute_tool_calls(
        self, tool_calls: List[Any], available_tools: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple tool calls and aggregate results.

        Args:
            tool_calls: List of tool call objects from LLM
            available_tools: Dictionary of available tools

        Returns:
            Dictionary with tools_used list and history entries
        """
        tool_results_for_history = []
        tools_used = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_ui.display_tool_call(tool_name)
            self.logger.info(f"Executing tool: {tool_call}")

            # Find full tool name
            tool_name_long = None
            for tool_info in list(available_tools.values()):
                if tool_info.get("name") == tool_name:
                    tool_name_long = (
                        f"{tool_info.get('server')}:{tool_info.get('name')}"
                    )
                    break

            if not tool_name_long:
                result_text = f"Error: Tool '{tool_name}' not found"
                tool_ui.display_tool_error(result_text)
            else:
                try:
                    # Parse and fix tool arguments
                    tool_args = json.loads(tool_call.function.arguments)
                    self.logger.info(f"Tool arguments: {tool_args}")

                    # Display tool input with styled UI
                    tool_ui.display_tool_input(tool_name_long, tool_args)
                    tool_ui.display_execution_status("executing")

                    # Fix tool arguments if needed
                    tool_args = fix_tool_args(
                        tools=available_tools,
                        tool_args=tool_args,
                        tool_name=tool_name_long,
                    )

                    # Execute tool call
                    result = await self._get_tool_response(
                        call_params=tool_args, tool_name=tool_name_long
                    )
                    result_text = result.model_dump()["content"][0]["text"]

                    # Display result with styled UI
                    tool_ui.display_execution_status("completed")
                    tool_ui.display_tool_result(result_text, max_length=500)

                except Exception as e:
                    error_msg = f"Tool execution failed: {e}"
                    tool_ui.display_tool_error(error_msg)
                    result_text = error_msg

            # Record tool call
            tools_used.append(tool_name_long or tool_name)

            # Add result to history
            tool_results_for_history.append(
                {
                    "role": "tool",
                    "content": result_text,
                    "tool_call_id": tool_call.id,
                }
            )

        return {"tools_used": tools_used, "history": tool_results_for_history}

    async def _get_tool_response(
        self,
        call_params: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
    ) -> CallToolResult:
        """
        Execute a single MCP tool call.

        Args:
            call_params: Parameters for the tool
            tool_name: Name of the tool to call

        Returns:
            CallToolResult from MCP server
        """
        try:
            self.logger.info(f"Connecting to MCP servers to call tool: {tool_name}")
            all_tools = await self.server_manager.connect_all_servers()

            if not all_tools:
                raise RuntimeError("No tools discovered")

            if tool_name and tool_name not in all_tools:
                raise ValueError(f"Tool '{tool_name}' not found")

            result = await self.server_manager.call_tool(
                tool_name, call_params or {}, use_cache=False
            )
            self.logger.info("Tool call executed successfully")
            return result

        finally:
            await self.server_manager.close_all_connections()

    async def _generate_final_response(self) -> str:
        """
        Generate final response after max iterations reached.

        Args:
            available_tools: List of available tools (empty to force final response)

        Returns:
            Final text response from LLM
        """
        # Show SUMMARIZING status
        from ui.status_manager import get_status_manager
        status_mgr = get_status_manager()
        status_mgr.set_summarizing("Synthesizing gathered information...")

        self.history.append(
            {
                "role": "user",
                "content": (
                    "You have reached the maximum tool call limit. "
                    "Please use the information gathered so far to generate your final answer."
                ),
            }
        )

        completion = self.client.chat.completions.create(
                    model=self.model_name, messages=self.history
                )
        final_content = completion.choices[0].message.content
        self.history.append({"role": "assistant", "content": final_content})

        status_mgr.clear()

        return final_content

    def _load_server_configs(self, config_path: str) -> List[Dict[str, Any]]:
        """
        Load MCP server configurations from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            List of server configuration dictionaries
        """
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        servers = []

        for name, conf in cfg.get("mcpServers", {}).items():
            if conf.get("transport") == "sse":
                servers.append(
                    {
                        "name": name,
                        "url": conf.get("url"),
                        "transport": conf.get("transport", "sse"),
                    }
                )
            else:
                servers.append(
                    {
                        "name": name,
                        "command": [conf.get("command")] + conf.get("args", []),
                        "env": conf.get("env"),
                        "cwd": conf.get("cwd"),
                        "transport": conf.get("transport", "stdio"),
                        "port": conf.get("port"),
                        "endpoint": conf.get("endpoint", "/mcp"),
                    }
                )

        return servers

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

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

        self.logger.info(f"Conversation exported to {output_file_path}")
        return output_file_path

    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        return self.system_prompt

    def append_history(
        self, history_episodes: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Append conversation episodes to history.

        Args:
            history_episodes: List of history dictionaries with 'role' and 'content'
        """
        if not history_episodes:
            return

        try:
            for episode in history_episodes:
                role = episode.get("role")
                if role and role in ("system", "user", "assistant"):
                    self.history.append(episode)
                else:
                    self.logger.error(f"Invalid role in history: {role}")
        except Exception as e:
            self.logger.error(f"Failed to append history: {e}")

    def clear_history(self) -> None:
        """Clear conversation history, keeping system prompt."""
        self.history = [{"role": "system", "content": self.system_prompt}]

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"model='{self.model_name}', "
            f"max_tools={self.max_tool_call}"
            f")"
        )
