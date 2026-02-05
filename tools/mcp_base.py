"""
MCP communication component for IntelliSearch.

This module provides a dedicated component for MCP protocol operations,
including tool discovery, execution, and response handling.
"""

import yaml
import json
import os
from typing import List, Dict, Any, Optional

from tools.server_manager import MultiServerManager
from mcp.types import CallToolResult
from ui.tool_ui import tool_ui
from core.tool_hash import fix_tool_args
from core.logger import get_logger


class MCPBase:
    """
    MCP communication component for tool management and execution.

    This class handles the communication with MCP servers, including tool discovery,
    execution, and response handling. It serves as a dedicated component for MCP
    protocol operations.

    Attributes:
        config_path: Path to MCP server configuration file
        config: Loaded server configurations
        server_manager: MCP server connection manager
        logger: Logger instance

    Example:
        >>> mcp_base = MCPBase(config_path="config/config.yaml")
        >>> tools = await mcp_base.list_tools()
        >>> result = await mcp_base.get_tool_response(
        ...     tool_name="search:google",
        ...     call_params={"query": "AI research"}
        ... )
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the MCPBase component.

        Args:
            config_path: Path to MCP server configuration file (YAML format)

        Raises:
            ValueError: If configuration file is invalid
        """
        self.config_path = config_path
        self.logger = get_logger(__name__)
        self.config = self._load_server_configs(config_path)
        self.server_manager = MultiServerManager(server_configs=self.config)
        self.logger.info("MCPBase initialized")

    def _load_server_configs(self, config_path: str) -> List[Dict[str, Any]]:
        """
        Load MCP server configurations from YAML file.

        Only loads servers that are specified in the 'server_choice' section
        of the configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            List of server configuration dictionaries

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        with open(config_path, "r", encoding="utf-8") as f:
            cfg: Dict = yaml.safe_load(f)

        servers = []
        all_servers: Dict = cfg.get("all_servers", {})
        server_choice: List[str] = cfg.get("server_choice", [])

        # If server_choice is empty, load all servers (backward compatibility)
        if not server_choice:
            self.logger.warning(
                "server_choice is empty, loading all servers. "
                "Please specify servers in server_choice to avoid loading unused servers."
            )
            server_choice = list(all_servers.keys())

        # Load only selected servers
        for name in server_choice:
            if name not in all_servers:
                self.logger.warning(
                    f"Server '{name}' in server_choice not found in all_servers, skipping"
                )
                continue

            conf = all_servers[name]

            # Build command list from command and args
            command = conf.get("command")
            args = conf.get("args")

            # Handle args as either string or list
            if isinstance(args, str):
                cmd_list = [command, args]
            elif isinstance(args, list):
                cmd_list = [command] + args
            else:
                cmd_list = [command]

            servers.append(
                {
                    "name": name,
                    "command": cmd_list,
                    "env": conf.get("env", {}),
                    "cwd": conf.get("cwd"),
                    "transport": conf.get("transport", "stdio"),
                    "port": conf.get("port"),
                    "endpoint": conf.get("endpoint", "/mcp"),
                }
            )

        self.logger.info(
            f"Loaded {len(servers)}/{len(all_servers)} server configurations "
            f"from server_choice: {server_choice}"
        )
        return servers

    async def list_tools(self) -> Dict[str, Any]:
        """
        Discover and list all available MCP tools.

        Returns:
            Dictionary mapping tool names to their configurations
        """
        try:
            self.logger.info("Discovering MCP tools...")
            all_tools = await self.server_manager.connect_all_servers()
            tool_save_path = "data/tools.json"
            if os.path.exists(tool_save_path):
                with open(tool_save_path, "w", encoding="utf-8") as file:
                    json.dump(all_tools, file, ensure_ascii=False, indent=2)

            if not all_tools:
                raise RuntimeError("No MCP tools discovered")

            return all_tools

        except Exception as e:
            self.logger.error(f"Failed to discover tools: {e}")
            return {}
        finally:
            await self.server_manager.close_all_connections()

    async def execute_tool_calls(
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
                    result = await self.get_tool_response(
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

    async def get_tool_response(
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
