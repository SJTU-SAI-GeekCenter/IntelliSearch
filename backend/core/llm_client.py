"""
LLM客户端核心模块,负责处理与语言模型的交互
"""
import os
import json
import asyncio
from config.config_loader import Config
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI

from .mcp_client import MCPClient
from core.tool_hash import fix_tool_args
from core.logger import get_logger


class LLMClient:
    """LLM客户端类，处理与AI模型的交互"""

    def __init__(
        self,
        model_name: str = "default_model",
        base_url: str = "EMPTY",
        api_key_env: str = "OPENAI_API_KEY"
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger(__name__)

        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(
                f"Environment variable '{api_key_env}' not found. Please set it."
            )

        self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        self.mcp_client = MCPClient()

    def format_tools_for_openai(self, tools: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将工具列表格式化为OpenAI API格式"""
        return [
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

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[Dict[str, Any]] = None,
        max_tool_calls: int = 20
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天完成，支持工具调用

        Yields:
            Dict: 包含类型和数据的字典
                - type: "content", "tool_call_start", "tool_call_delta", "tool_result", "error"
        """
        try:
            # 获取可用工具
            if tools is None:
                tools = await self.mcp_client.list_tools()

            available_tools = self.format_tools_for_openai(tools)
            self.logger.info(f"Available Tools: {len(tools)} tools loaded")

            # 处理工具调用循环
            for round_count in range(max_tool_calls):
                self.logger.info(f"Processing round {round_count + 1}")

                # 创建流式响应
                with self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=available_tools if available_tools else None,
                    stream=True,
                ) as stream:
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
                                    if tool_delta.index >= len(tool_calls):
                                        # 新工具调用
                                        tool_calls.append({
                                            "id": tool_delta.id,
                                            "type": "function",
                                            "function": {
                                                "name": tool_delta.function.name if tool_delta.function.name else "",
                                                "arguments": tool_delta.function.arguments if tool_delta.function.arguments else "",
                                            },
                                        })
                                        current_tool_call = tool_calls[-1]
                                        yield {
                                            "type": "tool_call_start",
                                            "tool_call": {
                                                "id": tool_delta.id,
                                                "name": tool_delta.function.name if tool_delta.function.name else "",
                                            },
                                        }
                                    else:
                                        # 更新现有工具调用
                                        current_tool_call = tool_calls[tool_delta.index]

                                    if tool_delta.function.name:
                                        current_tool_call["function"]["name"] = tool_delta.function.name
                                    if tool_delta.function.arguments:
                                        current_tool_call["function"]["arguments"] += tool_delta.function.arguments

                                    yield {
                                        "type": "tool_call_delta",
                                        "tool_call": {
                                            "id": current_tool_call["id"],
                                            "name": current_tool_call["function"]["name"],
                                            "arguments": tool_delta.function.arguments if tool_delta.function.arguments else "",
                                        },
                                    }

                # 检查是否需要执行工具调用
                if tool_calls:
                    # 添加助手消息到历史记录
                    assistant_message = {"role": "assistant", "tool_calls": tool_calls}
                    messages.append(assistant_message)

                    # 处理工具调用
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        self.logger.info(f"🚀 Executing tool: {tool_name}")

                        # 查找完整的工具名称
                        tool_name_long = None
                        for chunk in list(tools.values()):
                            if chunk.get("name") == tool_name:
                                tool_name_long = f"{chunk.get('server')}:{chunk.get('name')}"
                                break

                        if not tool_name_long:
                            tool_result_content = f"Error: Tool '{tool_name}' not found."
                        else:
                            try:
                                tool_args = json.loads(tool_call["function"]["arguments"])
                                self.logger.info(f"Tool args: {tool_args}")

                                # 修复工具参数
                                tool_args = fix_tool_args(
                                    tools=tools,
                                    tool_args=tool_args,
                                    tool_name=tool_name_long,
                                )

                                result = await self.mcp_client.call_tool(
                                    tool_name=tool_name_long,
                                    call_params=tool_args
                                )
                                tool_result_content = result.model_dump()["content"][0]["text"]
                            except Exception as e:
                                tool_result_content = f"Tool execution failed: {str(e)}"

                        # 添加工具结果到历史记录
                        tool_result = {
                            "role": "tool",
                            "content": tool_result_content,
                            "tool_call_id": tool_call["id"],
                        }
                        tool_results.append(tool_result)

                        yield {
                            "type": "tool_result",
                            "tool_result": {
                                "id": tool_call["id"],
                                "name": tool_name,
                                "result": tool_result_content,
                            },
                        }

                    messages.extend(tool_results)
                    continue
                else:
                    # 没有工具调用，结束对话
                    return

            # 超过工具调用限制
            self.logger.error(f"Tool calling limit exceeded: {max_tool_calls}")
            messages.append({
                "role": "user",
                "content": "Error: Maximum tool calling limit reached. Please use the information obtained to provide the final answer."
            })

            # 最终响应（无工具）
            with self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            ) as stream:
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if getattr(delta, "content", None):
                            yield {"type": "content", "content": delta.content}

        except Exception as e:
            error_message = f"Error calling LLM API: {e}"
            self.logger.error(error_message, exc_info=True)
            yield {"type": "error", "error": error_message}

    async def process_query_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        处理查询并以流式方式返回文本响应，适配FastAPI的StreamingResponse
        """
        async for event in self.chat_completion_stream(messages, tools):
            if event["type"] == "content":
                yield event["content"]
            elif event["type"] == "error":
                yield f"[LLM Error]: {event['error']}\n"

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """You name is Jiao-Xiao AI (交小AI), an intelligent agent launched by the Geek Center of the School of Artificial Intelligence, Shanghai Jiao Tong University. You can use various tools in multi-turn conversations to fulfill user requests, and you are not allowed to use markdown features like bold or italics.

ATTENTION! You are only allowed to call tools once per conversation round!"""