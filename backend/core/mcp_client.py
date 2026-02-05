"""
MCP客户端核心模块,负责处理MCP服务器连接和工具调用
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from tools.server_manager import MultiServerManager
from mcp.types import CallToolResult
from core.logger import get_logger


class MCPClient:
    """MCP客户端类，处理服务器连接和工具调用"""

    def __init__(self, config_path: str = "./config.json"):
        self.logger = get_logger(__name__)
        self.config_path = config_path
        self.config = self.load_server_configs(config_path)
        self.server_manager = MultiServerManager(server_configs=self.config)
        self.time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.result_dir = "./results"
        os.makedirs(self.result_dir, exist_ok=True)

    def load_server_configs(self, config_path: Path) -> List[Dict[str, Any]]:
        """从MCP config文件加载并转换server配置"""
        try:
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
                            "port": conf.get("port", None),
                            "endpoint": conf.get("endpoint", "/mcp"),
                        }
                    )
            return servers
        except Exception as e:
            self.logger.error(f"Failed to load server config: {e}")
            return []

    async def list_tools(self) -> Dict[str, Any]:
        """获取所有可用工具"""
        try:
            self.logger.info("🔌 Connecting and discovering tools...")
            all_tools = await self.server_manager.connect_all_servers()

            # 保存工具列表到文件
            with open(
                f"{self.result_dir}/{self.time_stamp}_list_tools.json",
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(all_tools, file, indent=4, ensure_ascii=False)

            if not all_tools:
                raise RuntimeError("No tools discovered.")
            return all_tools
        except Exception as e:
            self.logger.error(f"Error while connecting MCP Servers: {e}")
            return {}
        finally:
            await self.server_manager.close_all_connections()

    async def call_tool(
        self,
        tool_name: Optional[str] = None,
        call_params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """调用指定工具"""
        try:
            self.logger.info("🔌 Connecting and discovering tools...")
            all_tools = await self.server_manager.connect_all_servers()

            if not all_tools:
                raise RuntimeError("No tools discovered.")

            if tool_name is None:
                tool_name = next(iter(all_tools.keys()))
            if tool_name not in all_tools:
                raise ValueError(f"Tool '{tool_name}' not found.")

            self.logger.info(f"🚀 Calling tool: {tool_name}")
            result = await self.server_manager.call_tool(
                tool_name, call_params or {}, use_cache=False
            )
            self.logger.info("✅ Tool call SUCCESS.")
            return result

        finally:
            await self.server_manager.close_all_connections()