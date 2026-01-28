"""
IntelliSearch Evaluation Client

Optimized version for model evaluation without streaming output.
Focus on generating final answers with MCP tool integration.
"""
import os
import dotenv
import json
import logging
import asyncio
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from openai import OpenAI
from datetime import datetime
from tools.server_manager import MultiServerManager
from mcp.types import CallToolResult
from backend.tool_hash import fix_tool_args

# Load environment variables
dotenv.load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelliSearchEvalClient:
    """IntelliSearch evaluation client for model benchmarking with MCP tools."""

    def __init__(
        self,
        model_name: str = "deepseek-chat",
        system_prompt: str = "You are a helpful assistant",
        server_config_path: str = "./config.json",
        max_tool_call: int = 5,
    ):
        """Initialize the evaluation client.

        Args:
            model_name: Name of the model to use
            system_prompt: System prompt for the model
            server_config_path: Path to MCP server configuration
            max_tool_call: Maximum number of tool calls allowed
        """
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_tool_call = int(max_tool_call)

        # Setup OpenAI client
        self.base_url = os.environ.get("BASE_URL")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Environment variable 'OPENAI_API_KEY' not found. Please set it.")

        self.client = OpenAI(api_key=api_key, base_url=self.base_url)

        # Setup MCP server manager
        self.config_path = server_config_path
        self.config = self._load_server_configs(config_path=self.config_path)
        self.server_manager = MultiServerManager(server_configs=self.config)

        logger.info(f"IntelliSearch evaluation client initialized for model: {self.model_name}")

    def get_response(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Tuple[str, int]:
        """Get model response without streaming.

        Args:
            messages: List of conversation messages
            tools: Optional list of available tools

        Returns:
            Tuple of (response_text, total_tokens)
        """
        try:
            if tools:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    stream=False,
                    temperature=0.6,
                    top_p=0.95
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=False,
                    temperature=0.6,
                    top_p=0.95
                )

            content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens if response.usage else 0

            return content, total_tokens

        except Exception as e:
            logger.error(f"Error getting model response: {e}")
            return "", 0

    async def _list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools.

        Returns:
            Dictionary of available tools
        """
        try:
            logger.info("Connecting and discovering MCP tools...")
            all_tools = await self.server_manager.connect_all_servers()

            if not all_tools:
                logger.warning("No MCP tools discovered")
                return {}

            return all_tools
        except Exception as e:
            logger.error(f"Error while connecting MCP Servers: {e}")
            return {}
        finally:
            await self.server_manager.close_all_connections()

    def _load_server_configs(self, config_path: str) -> List[Dict[str, Any]]:
        """Load MCP server configurations from config file.

        Args:
            config_path: Path to the MCP configuration file

        Returns:
            List of server configurations
        """
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        servers = []

        for name, conf in cfg.get("mcpServers", {}).items():
            if conf.get("transport") == "sse":
                servers.append({
                    "name": name,
                    "url": conf.get("url"),
                    "transport": conf.get("transport", "sse"),
                })
            else:
                servers.append({
                    "name": name,
                    "command": [conf.get("command")] + conf.get("args", []),
                    "env": conf.get("env"),
                    "cwd": conf.get("cwd"),
                    "transport": conf.get("transport", "stdio"),
                    "port": conf.get("port", None),
                    "endpoint": conf.get("endpoint", "/mcp"),
                })
        return servers

    async def _get_tool_response(
        self,
        call_params: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute MCP tool call.

        Args:
            call_params: Parameters for the tool call
            tool_name: Name of the tool to call
            tools: Dictionary of available tools

        Returns:
            Tool execution result
        """
        try:
            if not tools:
                tools = await self._list_tools()

            if not tools:
                raise RuntimeError("No MCP tools discovered.")

            if tool_name is None:
                tool_name = next(iter(tools.keys()))
            if tool_name not in tools:
                raise ValueError(f"Tool '{tool_name}' not found.")

            logger.info(f"Executing MCP tool: {tool_name}")
            result = await self.server_manager.call_tool(
                tool_name, call_params or {}, use_cache=False
            )
            logger.info("Tool execution completed successfully")
            return result

        finally:
            await self.server_manager.close_all_connections()

    async def evaluate_query(self, user_query: str, system_prompt: Optional[str] = None) -> Tuple[str, int]:
        """Evaluate a query using MCP tools.

        Args:
            user_query: The user query to evaluate
            system_prompt: Optional system prompt override

        Returns:
            Tuple of (response_text, total_tokens)
        """
        # Build message history
        messages = [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": user_query}
        ]

        try:
            # Get available tools
            tools_dict = await self._list_tools()
            if not tools_dict:
                # No tools available, simple response
                logger.info("No MCP tools available, generating simple response")
                return self.get_response(messages)

            # Convert tools to OpenAI format
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "input_schema": tool.get("input_schema"),
                    },
                }
                for tool in tools_dict.values()
            ]

            # Process with tool calls
            total_tokens = 0
            for round_count in range(self.max_tool_call):
                logger.info(f"Processing evaluation round {round_count + 1}")

                # Get model response
                response_text, tokens = self.get_response(messages, available_tools)
                total_tokens += tokens

                # Get full response for tool call analysis
                if available_tools:
                    full_response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        tools=available_tools,
                        stream=False,
                        temperature=0.6,
                        top_p=0.95
                    )
                else:
                    # No more tool calls needed
                    return response_text, total_tokens

                # Check if tool calls are needed
                if full_response.choices[0].finish_reason == "tool_calls":
                    # Add assistant response to history
                    messages.append(full_response.choices[0].message.model_dump())

                    # Execute tool calls
                    for tool_call in full_response.choices[0].message.tool_calls:
                        tool_name = tool_call.function.name
                        logger.info(f"Executing tool: {tool_name}")

                        try:
                            # Find full tool name
                            tool_name_long = None
                            for tool_info in tools_dict.values():
                                if tool_info.get("name") == tool_name:
                                    tool_name_long = f"{tool_info.get('server')}:{tool_info.get('name')}"
                                    break

                            if not tool_name_long:
                                tool_result = f"Error: Tool '{tool_name}' not found"
                            else:
                                tool_args = json.loads(tool_call.function.arguments)
                                tool_args = fix_tool_args(
                                    tools=tools_dict,
                                    tool_args=tool_args,
                                    tool_name=tool_name_long,
                                )

                                result = await self._get_tool_response(
                                    call_params=tool_args,
                                    tool_name=tool_name_long,
                                    tools=tools_dict
                                )
                                tool_result = result.model_dump()["content"][0]["text"]

                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            tool_result = f"Tool execution failed: {e}"

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call.id,
                        })

                    continue
                else:
                    # Final response without tool calls
                    return response_text, total_tokens

            # Max tool calls reached
            logger.warning(f"Tool calling limit reached: {self.max_tool_call}")
            final_response, final_tokens = self.get_response(messages)
            return final_response, total_tokens + final_tokens

        except Exception as e:
            error_message = f"Evaluation error: {e}"
            logger.error(error_message, exc_info=True)
            return error_message, 0


# For compatibility with existing code
MCPChat = IntelliSearchEvalClient


if __name__ == "__main__":
    import argparse

    # Load system prompt
    try:
        with open("prompts/base_system_prompt.md", "r", encoding="utf-8") as file:
            SYSTEM_PROMPT = file.read()
    except FileNotFoundError:
        SYSTEM_PROMPT = "You are a helpful assistant with search capabilities."

    parser = argparse.ArgumentParser(description="IntelliSearch Evaluation Client")
    parser.add_argument("--model_name", type=str, default="deepseek-chat", help="Model name to use")
    parser.add_argument("--max_tool_calls", type=int, default=5, help="Maximum tool calls allowed")
    parser.add_argument("--system_prompt", type=str, default=SYSTEM_PROMPT, help="System prompt")
    parser.add_argument("--query", type=str, help="Query to evaluate")
    args = parser.parse_args()

    async def main():
        client = IntelliSearchEvalClient(
            model_name=args.model_name,
            system_prompt=args.system_prompt,
            max_tool_call=args.max_tool_calls,
        )

        if args.query:
            response, tokens = await client.evaluate_query(args.query)
            print(f"Response: {response}")
            print(f"Total tokens: {tokens}")
        else:
            # Interactive mode
            print("IntelliSearch Evaluation Client - Interactive Mode")
            print("Type 'exit' to quit")
            while True:
                try:
                    query = input("\nEnter your query: ")
                    if query.lower() == 'exit':
                        break

                    response, tokens = await client.evaluate_query(query)
                    print(f"\nResponse: {response}")
                    print(f"Tokens used: {tokens}")

                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")

    asyncio.run(main())
