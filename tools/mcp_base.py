"""
MCP communication component for IntelliSearch.

This module provides a dedicated component for MCP protocol operations,
including tool discovery, execution, and response handling.
"""

import yaml
import json
import os
import asyncio
import re
from typing import List, Dict, Any, Optional

from tools.server_manager import MultiServerManager
from mcp.types import CallToolResult
from core.UI.tool_ui import tool_ui
from tools.tool_hash import fix_tool_args
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
        self.logger = get_logger(__name__, "tool")
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

    @staticmethod
    def _extract_tool_result_text(result: Any) -> str:
        """Extract text from MCP tool result in a tolerant way."""
        if hasattr(result, "model_dump"):
            dumped = result.model_dump()
            if dumped.get("content") and len(dumped["content"]) > 0:
                return dumped["content"][0].get("text", "")
            return "(No string content returned)"

        if isinstance(result, dict):
            if "content" in result and len(result["content"]) > 0:
                return result["content"][0].get("text", "")
            if "error" in result:
                return f"Error: {result['error']}"
            return str(result)

        return str(result)

    @staticmethod
    def _extract_permission_request_payload(text: str) -> Optional[Dict[str, Any]]:
        """Parse PERMISSION_REQUEST marker payload from tool text."""
        marker = "PERMISSION_REQUEST::"
        if marker not in text:
            return None

        match = re.search(r"PERMISSION_REQUEST::(\{.*\})", text, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except Exception:
            return None

    @staticmethod
    def _apply_permission_from_form(values: Dict[str, Any], target_path: str) -> None:
        """Apply selected permission rule to operate_file security manager."""
        try:
            from mcp_server.operate_file.security import security_manager, AccessScope
        except ImportError:
            from .operate_file.security import security_manager, AccessScope  # type: ignore

        scope_map = {
            "Shallow": AccessScope.SHALLOW,
            "Recursive": AccessScope.RECURSIVE,
            "当前层级(Shallow)": AccessScope.SHALLOW,
            "递归(Recursive)": AccessScope.RECURSIVE,
        }
        ttl_map = {
            "Forever": None,
            "30 minutes": 30 * 60,
            "2 hours": 2 * 60 * 60,
            "永久": None,
            "30分钟": 30 * 60,
            "2小时": 2 * 60 * 60,
        }

        action = str(values.get("action", "read")).lower()
        allow_read = None
        allow_create = None
        allow_write = None
        allow_delete = None

        # 仅修改本次请求涉及的权限；其余权限保持 UNSET / 原值
        if action == "read":
            allow_read = True
        elif action == "create":
            allow_create = True
        elif action == "write":
            allow_write = True
        elif action == "delete":
            allow_delete = True

        from pathlib import Path

        target = Path(target_path).resolve()
        rule_target = target if target.is_dir() else target.parent

        scope_key = str(values.get("scope", "Recursive"))
        ttl_key = str(values.get("ttl", "Forever"))

        security_manager.add_permission(
            path=rule_target,
            scope=scope_map.get(scope_key, AccessScope.RECURSIVE),
            allow_read=allow_read,
            allow_create=allow_create,
            allow_write=allow_write,
            allow_delete=allow_delete,
            ttl_seconds=ttl_map.get(ttl_key, None),
            merge_existing=True,
        )

    @staticmethod
    def _apply_deny_from_form(
        values: Dict[str, Any], target_path: str, action: str
    ) -> None:
        """Persist explicit deny for current action when user selects reject."""
        try:
            from mcp_server.operate_file.security import security_manager, AccessScope
        except ImportError:
            from .operate_file.security import security_manager, AccessScope  # type: ignore

        ttl_map = {
            "Forever": None,
            "30 minutes": 30 * 60,
            "2 hours": 2 * 60 * 60,
            "永久": None,
            "30分钟": 30 * 60,
            "2小时": 2 * 60 * 60,
        }
        ttl_key = str(values.get("ttl", "Forever"))

        from pathlib import Path

        target = Path(target_path).resolve()
        rule_target = target if target.is_dir() else target.parent

        allow_read = None
        allow_create = None
        allow_write = None
        allow_delete = None

        action = str(action).lower()
        if action == "read":
            allow_read = False
        elif action == "create":
            allow_create = False
        elif action == "write":
            allow_write = False
        elif action == "delete":
            allow_delete = False

        scope_map = {
            "Shallow": AccessScope.SHALLOW,
            "Recursive": AccessScope.RECURSIVE,
            "当前层级(Shallow)": AccessScope.SHALLOW,
            "递归(Recursive)": AccessScope.RECURSIVE,
        }
        scope_key = str(values.get("scope", "Recursive"))

        security_manager.add_permission(
            path=rule_target,
            scope=scope_map.get(scope_key, AccessScope.RECURSIVE),
            allow_read=allow_read,
            allow_create=allow_create,
            allow_write=allow_write,
            allow_delete=allow_delete,
            ttl_seconds=ttl_map.get(ttl_key, None),
            merge_existing=True,
        )

    async def _handle_permission_request(
        self,
        payload: Dict[str, Any],
    ) -> bool:
        """Open Form in main CLI process and apply permission if granted."""
        from core.UI import UIEngine
        from core.UI.live import clear_live_layer

        target_path = payload.get("target_path", "")
        action = str(payload.get("action", "read")).lower()
        reason = payload.get("reason", "")

        action_label_map = {
            "read": "allow_read",
            "create": "allow_create",
            "write": "allow_write",
            "delete": "allow_delete",
        }
        action_label = action_label_map.get(action, f"allow_{action}")

        pages = [
            [
                {
                    "type": "select",
                    "key": "decision",
                    "message": "Authorize this filesystem request?",
                    "description": (
                        f"Target path: {target_path}\n"
                        f"Requested action: {action}\n"
                        f"Reason: {reason}\n\n"
                        "If you choose Allow, this form will modify ONLY:\n"
                        f"  - {action_label} = True\n"
                        "Other permissions remain UNSET/original values (not auto-denied).\n\n"
                        "If you choose Deny, this form will modify ONLY:\n"
                        f"  - {action_label} = False\n"
                        "Other permissions remain UNSET/original values."
                    ),
                    "options": ["Allow", "Deny"],
                    "default_index": 0,
                }
            ],
            [
                {
                    "type": "select",
                    "key": "scope",
                    "message": "Permission scope",
                    "description": "Tip: use Recursive for directories, Shallow for a narrow path.",
                    "options": ["Shallow", "Recursive"],
                    "default_index": 1,
                }
            ],
            [
                {
                    "type": "select",
                    "key": "ttl",
                    "message": "Permission duration",
                    "description": "Forever = no expiration; temporary grants expire automatically.",
                    "options": ["Forever", "30 minutes", "2 hours"],
                    "default_index": 0,
                }
            ],
        ]

        form_result = UIEngine.prompt_form(
            title="Filesystem Permission Request",
            pages=pages,
            allow_cancel=True,
        )

        # 立即释放表单占据空间，避免后续区域残留空白
        clear_live_layer("form")

        if not form_result.get("success") or not form_result.get("completed"):
            return False

        values = form_result.get("values", {})
        if values.get("decision") not in ("Allow", "允许"):
            # 用户拒绝时，仅写入本次 action 的显式拒绝，不影响其他权限
            self._apply_deny_from_form(values, target_path, action)
            return False

        # Let apply layer auto-infer permission profile from requested action
        values["action"] = action

        self._apply_permission_from_form(values, target_path)
        return True

    async def execute_tool_calls(
        self, tool_calls: List[Any], available_tools: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple tool calls and aggregate results.

        Args:
            tool_calls: List of tool call objects from LLM
            available_tools: Dictionary of available tools

        Returns:
            Dictionary with tools_used list, history entries, and detailed tool call info
        """
        tool_results_for_history = []
        tools_used = []
        tools_detailed = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args: Dict[str, Any] = {}
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
                    tool_ui.display_execution_status("executing")
                    tool_ui.display_tool_input(tool_name_long, tool_args)

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

                    # 检查 MCP 协议层面的工具执行错误
                    if getattr(result, "isError", False):
                        # 尝试从内容中提取错误信息
                        content = result.content if hasattr(result, "content") else []
                        error_texts = [
                            str(getattr(item, "text", ""))
                            for item in content
                            if getattr(item, "text", None) is not None
                        ]
                        full_error_msg = (
                            "\n".join(error_texts)
                            if error_texts
                            else "Unknown Tool Error"
                        )

                    # Safe result extraction
                    try:
                        result_text = self._extract_tool_result_text(result)
                    except Exception as extract_err:
                        self.logger.error(
                            f"Error extracting tool result: {extract_err} | Result type: {type(result)} | Result: {result}"
                        )
                        result_text = f"Error processing tool output: {extract_err}"

                    # Intercept permission request marker from operate_file and prompt user via Form in main process
                    permission_payload = self._extract_permission_request_payload(
                        result_text
                    )
                    if permission_payload:
                        granted = await self._handle_permission_request(
                            permission_payload
                        )
                        if granted:
                            retry_result = await self.get_tool_response(
                                call_params=tool_args, tool_name=tool_name_long
                            )
                            result_text = self._extract_tool_result_text(retry_result)
                        else:
                            result_text = "Permission denied by user."

                    # Display result with styled UI
                    tool_ui.display_execution_status("completed")
                    tool_ui.display_tool_result(result_text, max_length=500)

                except (KeyboardInterrupt, asyncio.CancelledError) as cancel_e:
                    # Tool execution was cancelled - propagate this to trigger cleanup
                    self.logger.info(
                        f"Tool execution cancelled: {type(cancel_e).__name__}"
                    )
                    raise cancel_e

                except Exception as e:
                    error_msg = str(e)
                    error_msg = f"Tool execution failed: {e}"
                    tool_ui.display_tool_error(error_msg)
                    result_text = error_msg

                # Record tool call with detailed info
                tools_used.append(tool_name_long or tool_name)

                # Store detailed tool call information for frontend
                tools_detailed.append(
                    {
                        "name": tool_name_long or tool_name,
                        "arguments": tool_args,
                        "result": result_text,
                        "success": not result_text.startswith("Error"),
                    }
                )

            # Add result to history
            tool_results_for_history.append(
                {
                    "role": "tool",
                    "content": result_text,
                    "tool_call_id": tool_call.id,
                }
            )

        return {
            "tools_used": tools_used,
            "history": tool_results_for_history,
            "tools_detailed": tools_detailed,
        }

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

            if not tool_name:
                raise ValueError("tool_name is required")

            result = await self.server_manager.call_tool(
                tool_name, call_params or {}, use_cache=False
            )
            # todo 此处的 info 加一个对 result 的截断显示
            self.logger.info("Tool call executed successfully")
            return result

        finally:
            await self.server_manager.close_all_connections()
