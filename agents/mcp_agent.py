"""
MCP-based Agent implementation for IntelliSearch.

This module provides an agent that leverages Model Context Protocol (MCP) tools
to enhance search and retrieval capabilities with multi-step reasoning.
"""

import os
import ast
import json
import asyncio
import re
import nest_asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from openai import OpenAI
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from tools.mcp_base import MCPBase
from memory.sequential import SequentialMemory
from core.logger import get_logger

# Type alias for status callback function
StatusCallback = Callable[[str, str], None]


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
        status_callback: Optional[StatusCallback] = None,
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
            status_callback: Optional callback function for status updates

        Raises:
            ValueError: If required configuration is missing
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
        self.logger = get_logger(__name__, "agent")
        self.logger.info(f"{self.name} initialized with model: {self.model_name}")

    def _notify_status(self, status_type: str, message: str) -> None:
        """
        Notify status changes to registered callback.

        This method allows the agent to report status updates without directly
        depending on UI modules. The caller can provide different callbacks
        for different environments (CLI, Web, testing, etc.).

        Args:
            status_type: Type of status update (e.g., "processing", "summarizing", "clear")
            message: Status message content
        """
        if self.status_callback:
            self.status_callback(status_type, message)

    def _should_force_rag(self, user_message: str) -> bool:
        """Determine whether to force a pre-retrieval RAG call.

        This hard constraint targets SJTU campus-context questions.
        """
        if not user_message:
            return False

        msg = user_message.lower()
        trigger_keywords = [
            "交大",
            "sjtu",
            "二月十三",
            "校庆",
            "校园卡",
            "喜饼",
            "一餐",
            "玉兰",
            "石楠",
            "归0",
            "交我办",
            "导师历",
            "东川鹿",
            "思源",
            "上院",
            "院士墙",
            "瑞幸",
            "碳基openclaw",
        ]
        return any(k in msg for k in trigger_keywords)

    async def _build_forced_rag_context(
        self, user_message: str, tools: Dict[str, Any]
    ) -> Optional[str]:
        """Force a semantic retrieval call and build compact context for the LLM."""
        tool_name = "search_file:search_semantic_local"

        if tool_name not in tools:
            self.logger.warning(
                f"Hard-RAG skipped: required tool '{tool_name}' is not available"
            )
            return None

        try:
            limit = int(os.environ.get("RAG_FORCE_LIMIT", "8"))
            threshold = float(os.environ.get("RAG_FORCE_THRESHOLD", "0.1"))

            result = await self.mcp_base.get_tool_response(
                call_params={
                    "query": user_message,
                    "limit": limit,
                    "threshold": threshold,
                },
                tool_name=tool_name,
            )

            raw_text = self.mcp_base._extract_tool_result_text(result)

            payload: Optional[Dict[str, Any]] = None
            try:
                payload = json.loads(raw_text)
            except Exception:
                # Many tool adapters return Python-dict-like strings
                try:
                    parsed = ast.literal_eval(raw_text)
                    if isinstance(parsed, dict):
                        payload = parsed
                except Exception:
                    payload = None

            if not payload or not payload.get("success"):
                return (
                    "[RAG预检索上下文]\n" "未检索到可用语料，回答时不要编造未命中事实。"
                )

            results = payload.get("results", []) or []
            if not results:
                return (
                    "[RAG预检索上下文]\n"
                    "当前语料未命中相关片段。请先给通用解释，并明确说明“语料未覆盖细节”。"
                )

            lines = [
                "[RAG预检索上下文]",
                "以下为系统强制预检索得到的本地语料片段。回答时优先参考这些片段，",
                "先给事实，再做轻量语境化表达（可幽默，但不过度扩写）。",
                "输出风格建议：语言自然，不要生硬套模板，不要强行塞梗词。",
            ]

            for idx, item in enumerate(results[:5], 1):
                text = str(item.get("text", "")).replace("\n", " ").strip()
                if len(text) > 240:
                    text = text[:240] + "..."
                score = item.get("score", "-")
                lines.append(f"{idx}. (score={score}) {text}")

            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Hard-RAG pre-retrieval failed: {e}", exc_info=True)
            return None

    def _build_style_guard_context(self) -> str:
        """Build explicit style guard to avoid overly rigid final responses."""
        return (
            "[回答风格硬约束]\n"
            "你是交大校园语境助手。最终回答要像靠谱同学，既自然也有温度。\n"
            "1) 先接住用户情绪，再给一句明确结论，再补1-3条关键点；\n"
            "2) 不要机械套“可能性分析/核验路径/经验参考”三段式标题；\n"
            "3) 校园话题且语料命中时，优先自然带入1-2个贴题梗词；语料未命中则不硬塞；\n"
            "4) 允许轻微幽默与共情，但必须像真人说话，避免做作和口号腔；\n"
            "5) 避免别扭称呼和病句（如“你20年”）；涉及年限时改成“你入学20年这个节点/你在交大20年这个节点”；\n"
            "6) 语料不足时明确说明“当前语料未覆盖细节”，不要硬编。"
        )

    @staticmethod
    def _coerce_dsml_value(raw: str) -> Any:
        """Best-effort conversion for DSML parameter string values."""
        text = (raw or "").strip()
        if text.lower() in {"true", "false"}:
            return text.lower() == "true"
        if re.fullmatch(r"-?\d+", text):
            try:
                return int(text)
            except Exception:
                return text
        if re.fullmatch(r"-?\d+\.\d+", text):
            try:
                return float(text)
            except Exception:
                return text
        return text

    def _parse_dsml_function_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse DSML-style function call text emitted by some models as plain content."""
        if not content or "<｜DSML｜invoke" not in content:
            return None

        invoke_match = re.search(r'<｜DSML｜invoke\s+name="([^"]+)"\s*>', content)
        if not invoke_match:
            return None

        name = invoke_match.group(1).strip()
        args: Dict[str, Any] = {}

        for p in re.finditer(
            r'<｜DSML｜parameter\s+name="([^"]+)"\s+string="[^"]*"\s*>(.*?)</｜DSML｜parameter>',
            content,
            re.DOTALL,
        ):
            key = p.group(1).strip()
            value = self._coerce_dsml_value(p.group(2))
            args[key] = value

        return {"name": name, "arguments": args}

    @staticmethod
    def _resolve_tool_full_name(
        tool_short_name: str, tools: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve short tool name to '<server>:<name>' full tool key."""
        for full_name, tool_info in tools.items():
            if tool_info.get("name") == tool_short_name:
                return full_name
        return None

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

        # Handle event loop properly - use nest_asyncio if loop is running
        try:
            # Check if there's a running event loop
            try:
                loop = asyncio.get_running_loop()
                # Use nest_asyncio to allow nested event loops
                nest_asyncio.apply()
                result = loop.run_until_complete(
                    self._process_query_async(
                        user_message=request.prompt,
                        max_iterations=max_iterations,
                    )
                )
            except RuntimeError:
                # No running event loop, safe to use asyncio.run
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

            # Check if the operation was cancelled
            if result.get("cancelled", False):
                return AgentResponse(
                    status="cancelled",
                    answer="Operation cancelled by user",
                    metadata={
                        "error": "User cancelled",
                        "error_type": "CancelledError",
                    },
                )

            # Add detailed tool call information for web UI
            if hasattr(self, "_tools_detailed"):
                response_metadata["tool_calls"] = self._tools_detailed
                # Clear for next request
                delattr(self, "_tools_detailed")

            return AgentResponse(
                status="success",
                answer=result.get("answer", ""),
                metadata=response_metadata,
            )

        except KeyboardInterrupt:
            # Handle KeyboardInterrupt - ensure cleanup
            self.logger.info("KeyboardInterrupt caught in inference")
            # Memory cleanup is already done in _process_query_async

            # Cancel all pending tasks in the event loop
            try:
                loop = asyncio.get_event_loop()
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
            except:
                pass  # Ignore errors during cleanup

            return AgentResponse(
                status="cancelled",
                answer="Operation cancelled by user",
                metadata={
                    "error": "KeyboardInterrupt",
                    "error_type": "KeyboardInterrupt",
                },
            )

        except RuntimeError as e:
            # Handle cancellation and other runtime errors
            error_text = str(e)

            # Check if this is a user cancellation
            if "cancelled by user" in error_text.lower():
                self.logger.info(f"User cancelled: {error_text}")
                return AgentResponse(
                    status="cancelled",
                    answer="Operation cancelled by user",
                    metadata={"error": error_text, "error_type": type(e).__name__},
                )
            else:
                self.logger.error(f"Inference failed: {e}", exc_info=True)
                return AgentResponse(
                    status="failed",
                    answer=f"Error during inference: {error_text}",
                    metadata={"error": error_text, "error_type": type(e).__name__},
                )

        except Exception as e:
            error_text = str(e)

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
        # Ensure memory is clean at start of each request
        # This handles cases where previous requests were cancelled
        if len(self.memory) > 1:  # More than just system prompt
            self.logger.info(
                f"Cleaning memory before new request (had {len(self.memory)} entries)"
            )
            self.memory.reset()

        # Discover available tools using MCPBase component
        tools = await self.mcp_base.list_tools()
        pre_retrieval_tools = dict(tools)

        # Keep semantic-local search for internal pre-retrieval only,
        # but hide it from LLM tool list to prevent explicit repeated calls.
        if "search_file:search_semantic_local" in tools:
            tools.pop("search_file:search_semantic_local", None)
            self.logger.info(
                "Tool hidden from LLM (internal pre-retrieval only): search_file:search_semantic_local"
            )

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

        tools_called = []
        final_answer = ""
        last_tool_signature: Optional[str] = None
        repeated_tool_signature_count = 0

        try:
            # Hard style guard: inject response-style constraints for every query
            self.memory.add(
                {"role": "system", "content": self._build_style_guard_context()}
            )

            # Hard constraint: keep one internal pre-retrieval per query
            forced_context = await self._build_forced_rag_context(
                user_message, pre_retrieval_tools
            )
            if forced_context:
                self.memory.add({"role": "system", "content": forced_context})

            # Add user message to memory inside try block to ensure cleanup on cancellation
            self.memory.add({"role": "user", "content": user_message})
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
                    tool_calls_safe = list(tool_call_lists or [])
                    allowed_tool_names = {
                        str(info.get("name", "")) for info in tools.values()
                    }

                    valid_tool_calls = []
                    invalid_tool_names = []
                    for tc in tool_calls_safe:
                        function_obj = getattr(tc, "function", None)
                        fn_name = str(getattr(function_obj, "name", "") or "").strip()
                        if fn_name in allowed_tool_names:
                            valid_tool_calls.append(tc)
                        else:
                            invalid_tool_names.append(fn_name)

                    if invalid_tool_names and not valid_tool_calls:
                        self.logger.warning(
                            f"Skipping invalid pseudo tool calls: {invalid_tool_names}"
                        )
                        self.memory.add(
                            {
                                "role": "system",
                                "content": (
                                    "你把格式标签当成了工具调用。"
                                    "注意：final_response/tool_tracing 只是输出标签，不是工具。"
                                    "请不要继续调用它们，直接输出自然语言答案。"
                                ),
                            }
                        )
                        continue

                    if invalid_tool_names and valid_tool_calls:
                        self.logger.warning(
                            f"Ignoring invalid tool calls and keeping valid ones: {invalid_tool_names}"
                        )
                        tool_calls_safe = valid_tool_calls

                    # Detect repeated identical tool-call pattern to avoid infinite loops
                    current_signature_parts = []
                    for tc in tool_calls_safe:
                        function_obj = getattr(tc, "function", None)
                        fn_name = getattr(function_obj, "name", "")
                        fn_args = getattr(function_obj, "arguments", "")
                        current_signature_parts.append(f"{fn_name}:{fn_args}")
                    current_tool_signature = "|".join(current_signature_parts)

                    if current_tool_signature == last_tool_signature:
                        repeated_tool_signature_count += 1
                    else:
                        repeated_tool_signature_count = 0
                        last_tool_signature = current_tool_signature

                    if repeated_tool_signature_count >= 1:
                        self.logger.warning(
                            "Detected repeated identical tool calls, forcing direct final answer"
                        )
                        self.memory.add(
                            {
                                "role": "system",
                                "content": (
                                    "检测到模型重复调用相同工具与参数。"
                                    "从现在开始禁止继续调用工具，请直接基于现有信息输出最终答案。"
                                ),
                            }
                        )

                        forced_completion = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=self.memory.get_view("chat_messages"),
                        )
                        forced_answer = (
                            forced_completion.choices[0].message.content or ""
                        )
                        self.memory.add({"role": "assistant", "content": forced_answer})
                        self._notify_status("clear", "")

                        return {
                            "answer": forced_answer,
                            "iterations": round_count + 1,
                            "tools_called": tools_called,
                            "tokens": {},
                        }

                    # Add assistant message to memory
                    self.memory.add(completion.choices[0].message.model_dump())

                    # Execute tool calls using MCPBase component
                    tool_results = await self.mcp_base.execute_tool_calls(
                        tool_calls_safe, tools
                    )

                    tools_called.extend(tool_results["tools_used"])

                    # Store detailed tool information for web UI
                    if "tools_detailed" in tool_results:
                        if not hasattr(self, "_tools_detailed"):
                            self._tools_detailed = []
                        self._tools_detailed.extend(tool_results["tools_detailed"])

                    self.memory.add_many(tool_results["history"])
                    continue

                else:
                    content_text = completion.choices[0].message.content or ""

                    # Fallback: some models output DSML-style function call text instead of native tool_calls
                    dsml_call = self._parse_dsml_function_call(content_text)
                    if dsml_call:
                        tool_short_name = dsml_call.get("name", "")
                        tool_args = dsml_call.get("arguments", {})
                        tool_full_name = self._resolve_tool_full_name(
                            tool_short_name, tools
                        )

                        if tool_full_name:
                            self.logger.warning(
                                f"Detected DSML pseudo tool call, executing fallback for {tool_full_name}"
                            )
                            result = await self.mcp_base.get_tool_response(
                                call_params=tool_args,
                                tool_name=tool_full_name,
                            )
                            result_text = self.mcp_base._extract_tool_result_text(
                                result
                            )
                            tools_called.append(tool_full_name)

                            # Store compact execution trace and ask model to continue in normal natural language
                            self.memory.add(
                                {
                                    "role": "assistant",
                                    "content": (
                                        f"[已识别工具请求] {tool_short_name}({json.dumps(tool_args, ensure_ascii=False)})"
                                    ),
                                }
                            )
                            self.memory.add(
                                {
                                    "role": "system",
                                    "content": (
                                        f"[工具执行结果 {tool_full_name}] {result_text}\n"
                                        "请基于该结果继续回答。不要输出 DSML/function_calls 标签，"
                                        "直接输出自然语言最终答案。"
                                    ),
                                }
                            )
                            continue

                    # LLM completed without tool calls - notify summarizing status

                    self._notify_status("summarizing", "Generating final response...")

                    final_answer = content_text
                    self.memory.add({"role": "assistant", "content": final_answer})

                    self._notify_status("clear", "")

                    return {
                        "answer": final_answer,
                        "iterations": round_count + 1,
                        "tools_called": tools_called,
                        "tokens": {},
                    }

            # Max iterations reached
            self.logger.info(f"Max tool call limit reached: {max_iterations}")
            self._notify_status(
                "warning",
                f"Reached maximum tool call limit ({max_iterations}), generating final response...",
            )
            final_answer = await self._generate_final_response()

            return {
                "answer": final_answer,
                "iterations": max_iterations,
                "tools_called": tools_called,
                "tokens": {},
            }

        except (KeyboardInterrupt, asyncio.CancelledError) as cancel_e:
            # User cancelled the operation - clean up state
            self.logger.info(
                f"Query processing was cancelled by user: {type(cancel_e).__name__}"
            )
            # Force reset memory to clear any partial state
            self.memory.reset()
            self.logger.debug("Memory has been reset after cancellation")
            # Clear any partial tool results
            if hasattr(self, "_tools_detailed"):
                delattr(self, "_tools_detailed")
                self.logger.debug("Cleared partial tool results")
            # Return cancelled status instead of raising - this prevents exception from propagating to event loop
            return {
                "answer": "Operation cancelled by user",
                "iterations": 0,
                "tools_called": [],
                "tokens": {},
                "cancelled": True,
            }

        except Exception as e:
            error_text = str(e)

            error_message = f"Error during query processing: {e}"
            self.logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message)

    async def _generate_final_response(self) -> str:
        """
        Generate final response after max iterations reached.

        Returns:
            Final text response from LLM
        """
        # Notify summarizing status
        self._notify_status("summarizing", "头脑风暴中...")

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

        self._notify_status("clear", "")

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
