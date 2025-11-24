# * CLI version of IntelliSearch
import os
import dotenv
import json
import logging
import asyncio
import argparse
import sys


sys.path.append(os.getcwd())
# set up logging config
from utils.log_config import setup_logging

logging.getLogger("mcp").setLevel(logging.CRITICAL)


from pathlib import Path
from openai import OpenAI
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from mcp_module.server_manager import MultiServerManager
from mcp.types import CallToolResult
from colorama import Fore, Style, init
from prompt_toolkit import prompt
from rich.console import Console
from backend.tool_hash import fix_tool_args


init(autoreset=True)
dotenv.load_dotenv()
setup_logging(log_file_path="./log/mcp.log", project_prefix="IntelliSearch Main")


class MCPChat:
    def __init__(
        self,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        system_prompt: str = "You are a helpful assistant",
        server_config_path: str = "./config.json",
        max_tool_call: int = 5,
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.history = []
        self.system_prompt = system_prompt
        self.history.append({"role": "system", "content": system_prompt})
        self.time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.result_dir = "./results"
        self.max_tool_call = int(max_tool_call)
        os.makedirs(self.result_dir, exist_ok=True)

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "Environment variable 'DEEPSEEK_API_KEY' not found. Please set it."
            )

        self.client = OpenAI(api_key=api_key, base_url=self.base_url)

        # handle mcp settings and connecting mcp servers
        self.config_path = server_config_path
        self.config = self.load_server_configs(config_path=self.config_path)
        self.server_manager = MultiServerManager(server_configs=self.config)
        # list all the tools available
        self.available_tools = []

        # setup logger
        self.logger = logging.getLogger(__name__)
        TOOL_CALL_ERROR = 35
        logging.addLevelName(TOOL_CALL_ERROR, "TOOL CALL ERROR")
        self.logger.info(
            f"DeepSeek Chat with MCP enhancement client initialized for model: {self.model_name}"
        )

    def stream_chat_response(self, available_tools):
        """
        执行流式响应逻辑（同步版本，兼容 DeepSeek / OpenAI SDK）
        """
        result_text = ""
        if available_tools:
            with self.client.chat.completions.stream(
                model=self.model_name,
                messages=self.history,
                tools=available_tools,
            ) as stream:
                for event in stream:
                    if hasattr(event, "chunk") and event.chunk.choices:
                        delta = event.chunk.choices[0].delta

                        if getattr(delta, "content", None):
                            print(
                                Style.BRIGHT + Fore.YELLOW + delta.content,
                                end="",
                                flush=True,
                            )
                            result_text += delta.content

                        if getattr(delta, "tool_calls", None):
                            for tool in delta.tool_calls:
                                func = getattr(tool, "function", None)
                                if func:
                                    if func.name:
                                        print(
                                            Fore.GREEN + f"\n🔧 Tool name: {func.name}"
                                        )
                                    if func.arguments:
                                        print(
                                            Fore.GREEN + func.arguments,
                                            end="",
                                            flush=True,
                                        )

                final_message = stream.get_final_completion()
                return result_text, final_message
        else:
            # no tools for streaming response
            with self.client.chat.completions.stream(
                model=self.model_name,
                messages=self.history,
            ) as stream:
                for event in stream:
                    if hasattr(event, "chunk") and event.chunk.choices:
                        delta = event.chunk.choices[0].delta

                        if getattr(delta, "content", None):
                            print(
                                Style.BRIGHT + Fore.YELLOW + delta.content,
                                end="",
                                flush=True,
                            )
                            result_text += delta.content

                        if getattr(delta, "tool_calls", None):
                            for tool in delta.tool_calls:
                                func = getattr(tool, "function", None)
                                if func:
                                    if func.name:
                                        print(
                                            Fore.GREEN + f"\n🔧 Tool name: {func.name}"
                                        )
                                    if func.arguments:
                                        print(
                                            Fore.GREEN + func.arguments,
                                            end="",
                                            flush=True,
                                        )

                final_message = stream.get_final_completion()
                return result_text, final_message

    async def chat_completion_stream(
        self, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        真正的异步流式处理函数，yield 每一个来自 OpenAI SDK 的 delta
        支持多轮工具调用

        Yields:
            Dict[str, Any]: 包含以下可能的键:
                - type: "content" (文本内容) 或 "tool_call" (工具调用) 或 "tool_result" (工具结果)
                - content: 文本内容 (当 type 为 "content" 时)
                - tool_call: 工具调用信息 (当 type 为 "tool_call" 时)
                - tool_result: 工具执行结果 (当 type 为 "tool_result" 时)
        """
        try:
            # 获取可用工具
            tools = await self.list_tools()
            self.logger.info(f"Available Tools: {tools}")
            self.tools_store = tools
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": f"{tool.get('name')}",
                        "description": tool.get("description"),
                        "input_schema": tool.get("input_schema"),
                    },
                }
                for tool in list(tools.values())
            ]

            # 添加用户消息到历史记录
            self.history.append({"role": "user", "content": user_message})

            # 处理工具调用循环
            for round_count in range(self.max_tool_call):
                self.logger.info(f"Calling tool response for round: {round_count + 1}")

                # 创建流式响应
                if available_tools:
                    with self.client.chat.completions.create(
                        model=self.model_name,
                        messages=self.history,
                        tools=available_tools,
                        stream=True,
                    ) as stream:
                        # 收集工具调用
                        tool_calls = []
                        current_tool_call = None

                        # 处理流式响应
                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta:
                                delta = chunk.choices[0].delta

                                # 处理内容
                                if getattr(delta, "content", None):
                                    yield {"type": "content", "content": delta.content}

                                # 处理工具调用
                                if getattr(delta, "tool_calls", None):
                                    for tool_delta in delta.tool_calls:
                                        # 如果是新工具调用的开始
                                        if tool_delta.index >= len(tool_calls):
                                            tool_calls.append(
                                                {
                                                    "id": tool_delta.id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": (
                                                            tool_delta.function.name
                                                            if tool_delta.function.name
                                                            else ""
                                                        ),
                                                        "arguments": (
                                                            tool_delta.function.arguments
                                                            if tool_delta.function.arguments
                                                            else ""
                                                        ),
                                                    },
                                                }
                                            )
                                            current_tool_call = tool_calls[-1]
                                            # 发送工具调用开始信号
                                            yield {
                                                "type": "tool_call_start",
                                                "tool_call": {
                                                    "id": tool_delta.id,
                                                    "name": (
                                                        tool_delta.function.name
                                                        if tool_delta.function.name
                                                        else ""
                                                    ),
                                                },
                                            }
                                        else:
                                            # 更新现有工具调用
                                            current_tool_call = tool_calls[
                                                tool_delta.index
                                            ]

                                        # 更新工具调用信息
                                        if tool_delta.function.name:
                                            current_tool_call["function"][
                                                "name"
                                            ] = tool_delta.function.name
                                        if tool_delta.function.arguments:
                                            current_tool_call["function"][
                                                "arguments"
                                            ] += tool_delta.function.arguments

                                        # 发送工具调用更新
                                        yield {
                                            "type": "tool_call_delta",
                                            "tool_call": {
                                                "id": current_tool_call["id"],
                                                "name": current_tool_call["function"][
                                                    "name"
                                                ],
                                                "arguments": (
                                                    tool_delta.function.arguments
                                                    if tool_delta.function.arguments
                                                    else ""
                                                ),
                                            },
                                        }
                else:
                    # 没有工具的流式响应
                    with self.client.chat.completions.create(
                        model=self.model_name, messages=self.history, stream=True
                    ) as stream:
                        # 处理流式响应
                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta:
                                delta = chunk.choices[0].delta
                                if getattr(delta, "content", None):
                                    yield {"type": "content", "content": delta.content}

                # 检查是否需要工具调用
                if tool_calls:
                    # 添加助手消息到历史记录
                    assistant_message = {"role": "assistant", "tool_calls": tool_calls}
                    self.history.append(assistant_message)

                    # 处理每个工具调用
                    tool_results_for_history = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        print("\n" + f"🚀Calling Tools {tool_name}" + "\n")
                        self.logger.info(f"Calling tools: {tool_call}")

                        tool_name_long = None
                        for chunk in list(tools.values()):
                            if chunk.get("name") == tool_name:
                                tool_name_long = (
                                    f"{chunk.get('server')}:{chunk.get('name')}"
                                )
                                break

                        if not tool_name_long:
                            tool_result_content = (
                                f"Error: Tool '{tool_name}' not found."
                            )
                        else:
                            try:
                                tool_args = json.loads(
                                    tool_call["function"]["arguments"]
                                )
                                self.logger.info(f"Tool Calling args: {tool_args}")
                                # 修复工具参数
                                tool_args = fix_tool_args(
                                    tools=tools,
                                    tool_args=tool_args,
                                    tool_name=tool_name_long,
                                )
                                result: CallToolResult = await self.get_tool_response(
                                    call_params=tool_args, tool_name=tool_name_long
                                )
                                tool_result_content = result.model_dump()["content"][0][
                                    "text"
                                ]
                            except Exception as tool_e:
                                tool_result_content = f"Tool execution failed: {tool_e}"

                        # 添加工具结果到历史记录
                        tool_result_entry = {
                            "role": "tool",
                            "content": tool_result_content,
                            "tool_call_id": tool_call["id"],
                        }
                        tool_results_for_history.append(tool_result_entry)

                        # 发送工具结果
                        yield {
                            "type": "tool_result",
                            "tool_result": {
                                "id": tool_call["id"],
                                "name": tool_name,
                                "result": tool_result_content,
                            },
                        }

                    # 扩展历史记录
                    self.history.extend(tool_results_for_history)
                    continue
                else:
                    # 没有工具调用，结束对话
                    return

            # 超过工具调用限制
            self.logger.error(f"Tool calling limits for {self.max_tool_call} times")
            self.history.append(
                {
                    "role": "user",
                    "content": "Error, you have reached the maximum limit of tool calling requests. Please use the information you get by the tools to generate the final answer.",
                }
            )

            # 不带工具调用的最终响应
            with self.client.chat.completions.create(
                model=self.model_name, messages=self.history, stream=True
            ) as stream:
                # 处理最终响应
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if getattr(delta, "content", None):
                            yield {"type": "content", "content": delta.content}

            return

        except Exception as e:
            error_message = f"Error calling LLM API: {e}"
            self.logger.error(error_message, exc_info=True)
            yield {"type": "error", "error": error_message}

    async def process_query_stream(
        self, user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        处理查询并以流式方式返回响应，适配FastAPI的StreamingResponse
        """
        async for event in self.chat_completion_stream(user_message):
            if event["type"] == "content":
                # 直接yield文本内容
                yield event["content"]
            elif event["type"] == "error":
                # 错误信息
                yield f"[LLM Error]: {event['error']}\n"
            # 其他类型事件(工具调用等)可以选择性处理或忽略

    async def list_tools(self):
        try:
            self.logger.info("🔌 Connecting and discovering tools...")
            all_tools = await self.server_manager.connect_all_servers()
            with open(
                f"./results/{self.time_stamp}_list_tools.json", "w", encoding="utf-8"
            ) as file:
                json.dump(all_tools, file, indent=4, ensure_ascii=False)

            if not all_tools:
                raise RuntimeError("No tools discovered.")
            return all_tools
        except Exception as e:
            self.logger.error(f"Error while connecting MCP Servers: {e}")
            return []
        finally:
            await self.server_manager.close_all_connections()

    # async def process

    def load_server_configs(self, config_path: Path):
        """从 MCP config 文件加载并转换 server 配置"""
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

    async def get_tool_response(
        self,
        call_params: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
    ) -> Any:
        """连接 MCP server 并调用工具，返回结果"""
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

    def get_system_prompt(self):
        return self.system_prompt

    def append_history(self, append_history: Optional[List[Dict[str, str]]] = None):
        if append_history:
            try:
                for history_episode in append_history:
                    role = history_episode.get("role", None)
                    if role and role in ("system", "user", "assistant"):
                        self.history.append(history_episode)
                    else:
                        self.logger.error(f"Error for role: {role}")
            except Exception as e:
                self.logger.error(f"Updating History Failed: {e}")

    async def process_query(self, user_message: str, stream: bool = True):
        tools = await self.list_tools()
        self.logger.info(f"Available Tools: {tools}")
        self.tools_store = tools
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": f"{tool.get("name")}",
                    "description": tool.get("description"),
                    "input_schema": tool.get("input_schema"),
                },
            }
            for tool in list(tools.values())
        ]

        # getting self.history
        self.history.append({"role": "user", "content": user_message})

        try:
            for round_count in range(self.max_tool_call):
                # *fix: older version for non-streaming output
                # response = self.client.chat.completions.create(
                #     model=self.model_name,
                #     messages=self.history,
                #     tools=available_tools,
                #     stream=False,
                # )
                self.logger.info(f"Calling tool response for round: {round_count + 1}")
                final_text, response = self.stream_chat_response(
                    available_tools=available_tools
                )

                content = response.choices[0]
                if content.finish_reason == "tool_calls":
                    self.history.append(content.message.model_dump())
                    tool_results_for_history = []
                    for tool_call_single in content.message.tool_calls:

                        # tool_call_single = content.message.tool_calls[0]
                        tool_name = tool_call_single.function.name
                        print("\n" + f"🚀Calling Tools {tool_name}" + "\n")
                        self.logger.info(f"Calling tools: {tool_call_single}")

                        tool_name_long = None
                        for chunk in list(tools.values()):
                            if chunk.get("name") == tool_name:
                                tool_name_long = (
                                    f"{chunk.get("server")}:{chunk.get("name")}"
                                )
                                break

                        if not tool_name_long:
                            tool_result_content = (
                                f"Error: Tool '{tool_name}' not found."
                            )
                        else:
                            try:
                                tool_args = json.loads(
                                    tool_call_single.function.arguments
                                )
                                self.logger.info(f"Tool Calling args: {tool_args}")
                                # pass add fix for tool names and tool_args
                                tool_args = fix_tool_args(
                                    tools=tools,
                                    tool_args=tool_args,
                                    tool_name=tool_name_long,
                                )
                                result: CallToolResult = await self.get_tool_response(
                                    call_params=tool_args, tool_name=tool_name_long
                                )
                                tool_result_content = result.model_dump()["content"][0][
                                    "text"
                                ]
                            except Exception as tool_e:
                                tool_result_content = f"Tool execution failed: {tool_e}"

                        # add tool result into message lists
                        tool_results_for_history.append(
                            {
                                "role": "tool",
                                "content": tool_result_content,
                                "tool_call_id": tool_call_single.id,
                            }
                        )
                    self.history.extend(tool_results_for_history)
                    continue

                else:
                    # LLM finish calling tools, will return the final response
                    final_content = response.choices[0].message.content
                    self.history.append({"role": "assistant", "content": final_content})
                    return final_content

            # exceed tool calling limit
            self.logger.error(f"Tool calling limits for {self.max_tool_call} times")
            self.history.append(
                {
                    "role": "user",
                    "content": "Error, you have reached the maximum limit of tool calling requests. Please use the information you get by the tools to generate the final answer.",
                }
            )
            # let llm answer the questions without giving the tools
            # response = self.client.chat.completions.create(
            #     model=self.model_name,
            #     messages=self.history,
            #     # no tools given
            #     stream=False,
            # )
            final_text, response = self.stream_chat_response(available_tools=[])

            # get final result
            final_content = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": final_content})
            return final_content

        except Exception as e:
            error_message = f"Error calling LLM API: {e}"
            self.logger.error(error_message, exc_info=True)

            if stream:
                return (chunk for chunk in [f"[LLM Error]: {error_message}\n"])
            else:
                raise RuntimeError(error_message)

    def export_message(self, output_file_path: str = None):
        pass
        if not output_file_path:
            output_file_path = os.path.join(
                self.result_dir, f"./{self.time_stamp}_memory.json"
            )
        dir, file = os.path.split(output_file_path)
        os.makedirs(dir, exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as file:
            json.dump(self.history, file, ensure_ascii=False, indent=4)
            self.logger.info(f"Successfully writing messages into {output_file_path}")


async def query(chat_client: MCPChat, user_query):
    console.print("\n" + "[bold green]✨ Model Response:[/bold green]")
    result = await chat_client.process_query(
        user_message=user_query,
        stream=False,
    )
    chat_client.export_message()
    print("\n\n")
    # console.print("\n\n" + result + "\n\n")


if __name__ == "__main__":
    SYSTME_PROMPT = "You name is Jiao-Xiao AI (交小AI), an intelligent agent launched by the Geek Center of the School of Artificial Intelligence, Shanghai Jiao Tong University. You can use various tools in multi-turn conversations to fulfill user requests, and you are not allowed to use markdown features like bold or italics.\n ATTENTION! 每一轮对话你只允许调用一轮工具！"
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="deepseek-chat")
    parser.add_argument("--max_tool_calls", type=int, default=10)
    parser.add_argument("--system_prompt", type=str, default=SYSTME_PROMPT)
    args = parser.parse_args()

    console = Console()
    chat_client = MCPChat(
        model_name=args.model_name,
        system_prompt=args.system_prompt,
        max_tool_call=args.max_tool_calls,
    )
    while True:
        user_input = prompt("Input your query: ")
        if str(user_input).lower() in ("exit", "quit", "q"):
            console.print("[bold red]Exiting... Goodbye! 👋[/bold red]")
            break
        asyncio.run(query(chat_client=chat_client, user_query=user_input))
