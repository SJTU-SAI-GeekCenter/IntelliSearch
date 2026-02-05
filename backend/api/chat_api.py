"""
IntelliSearch 聊天API服务 - 支持真正的流式输出
基于LLMClient实现真实的流式响应
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 添加项目根目录到路径
sys.path.append(os.getcwd())
from config.config_loader import Config

# Load environment variables from config.yaml
config = Config.get_instance()

from backend.core.llm_client import LLMClient
from core.logger import get_logger

# 配置日志
logging.getLogger("mcp").setLevel(logging.CRITICAL)
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/chat", tags=["chat"])

# 请求模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_tools: bool = True
    model_name: Optional[str] = "deepseek-chat"
    max_tool_calls: Optional[int] = 5
    system_prompt: Optional[str] = None

# 存储会话
sessions: Dict[str, LLMClient] = {}

# 加载默认系统提示词
def load_system_prompt():
    """加载系统提示词"""
    try:
        with open("prompts/base_system_prompt.md", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "You are a helpful assistant with access to various tools."


def get_or_create_session(session_id: Optional[str] = None, **kwargs) -> str:
    """获取或创建会话"""
    if session_id and session_id in sessions:
        return session_id

    # 创建新会话ID
    new_session_id = session_id or str(uuid.uuid4())

    # 创建新的LLM客户端
    system_prompt = kwargs.get('system_prompt') or load_system_prompt()
    model_name = kwargs.get('model_name', 'deepseek-chat')
    max_tool_calls = kwargs.get('max_tool_calls', 20)

    try:
        # 获取base_url和api_key配置
        base_url = os.environ.get("BASE_URL", "https://api.deepseek.com")
        api_key_env = "OPENAI_API_KEY"

        chat_client = LLMClient(
            model_name=model_name,
            base_url=base_url,
            api_key_env=api_key_env
        )

        # 设置系统提示词和最大工具调用次数
        chat_client.system_prompt = system_prompt
        chat_client.max_tool_calls = max_tool_calls

        sessions[new_session_id] = chat_client
        logger.info(f"Created new session: {new_session_id}")
    except Exception as e:
        logger.error(f"Failed to create session {new_session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    return new_session_id


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """格式化SSE事件"""
    event_data = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        **data
    }
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


async def stream_chat_process(chat_client: LLMClient, user_message: str) -> AsyncGenerator[str, None]:
    """
    真正的流式聊天处理 - 基于LLMClient的流式实现
    """
    try:
        # 发送开始事件
        yield format_sse_event("start", {"message": "开始处理您的请求..."})

        # 列出可用工具
        yield format_sse_event("tools_discovery", {"message": "🔌 正在连接和发现工具..."})

        tools = await chat_client.mcp_client.list_tools()
        if not tools:
            yield format_sse_event("warning", {"message": "未发现可用工具"})

        chat_client.logger.info(f"Available Tools: {tools}")

        yield format_sse_event("tools_ready", {
            "message": f"✅ 发现 {len(tools)} 个可用工具",
            "tools_count": len(tools)
        })

        # 准备消息历史，包含系统提示词和用户消息
        messages = [
            {"role": "system", "content": chat_client.system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 处理查询 - 使用真正的流式响应
        tool_call_count = 0
        max_tool_calls = getattr(chat_client, 'max_tool_calls', 20)

        async for event in chat_client.chat_completion_stream(messages, tools, max_tool_calls):
            event_type = event["type"]

            if event_type == "content":
                # 真正的流式内容输出
                yield format_sse_event("content", {
                    "content": event["content"]
                })

            elif event_type == "tool_call_start":
                tool_call_count += 1
                tool_call = event["tool_call"]
                yield format_sse_event("tool_call_start", {
                    "message": f"🛠️ 调用工具: {tool_call['name']}",
                    "tool_call": tool_call,
                    "tool_index": tool_call_count,
                    "round": 1  # LLMClient内部处理轮次
                })

            elif event_type == "tool_call_delta":
                tool_call = event["tool_call"]
                yield format_sse_event("tool_call_delta", {
                    "tool_call": tool_call
                })

            elif event_type == "tool_result":
                tool_result = event["tool_result"]
                # 处理工具结果截断
                result_content = tool_result["result"]
                if len(result_content) > 500:
                    truncated_result = result_content[:500] + "...(已截断)"
                    yield format_sse_event("tool_result", {
                        "message": "✅ 工具执行结果 (已截断):",
                        "tool_name": tool_result["name"],
                        "result": truncated_result,
                        "full_length": len(result_content),
                        "truncated": True
                    })
                else:
                    yield format_sse_event("tool_result", {
                        "message": "✅ 工具执行结果:",
                        "tool_name": tool_result["name"],
                        "result": result_content,
                        "full_length": len(result_content),
                        "truncated": False
                    })

            elif event_type == "error":
                yield format_sse_event("error", {
                    "message": f"❌ 处理错误: {event['error']}"
                })

        yield format_sse_event("session_complete", {
            "message": "🎉 对话完成"
        })

    except Exception as e:
        logger.error(f"Error in stream_chat_process: {e}", exc_info=True)
        yield format_sse_event("error", {
            "message": f"❌ 处理过程中发生错误: {str(e)}",
            "error": str(e)
        })

    finally:
        # 确保清理MCP连接
        try:
            await chat_client.mcp_client.server_manager.close_all_connections()
        except Exception as e:
            logger.error(f"Error closing MCP connections: {e}")


@router.post("")
@router.post("/")
async def chat(request: ChatRequest):
    """非流式聊天接口"""

    try:
        # 获取或创建会话
        session_id = get_or_create_session(
            session_id=request.session_id,
            model_name=request.model_name,
            max_tool_calls=request.max_tool_calls,
            system_prompt=request.system_prompt
        )

        # 简单的对话响应（不流式）
        response = ""
        if not request.use_tools:
            response = "你好！我是IntelliSearch智能助手。我可以帮助您进行各种搜索和信息查询。如需使用搜索功能，请在请求中设置 use_tools=true。"
        else:
            response = "您好！我是IntelliSearch智能助手，配备了强大的搜索工具。请告诉我您想搜索什么信息？"

        return {"content": response, "session_id": session_id}

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """增强的流式聊天接口"""

    try:
        # 获取或创建会话
        session_id = get_or_create_session(
            session_id=request.session_id,
            model_name=request.model_name,
            max_tool_calls=request.max_tool_calls,
            system_prompt=request.system_prompt
        )

        chat_client = sessions[session_id]

        async def generate():
            """生成SSE流式响应"""
            try:
                async for event in stream_chat_process(chat_client, request.message):
                    yield event

                # 发送结束标记
                yield format_sse_event("done", {"message": "会话结束"})
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Error in generate: {e}")
                yield format_sse_event("error", {"message": f"生成响应时发生错误: {str(e)}"})
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        logger.error(f"Error in chat_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # 清理MCP连接
        await sessions[session_id].mcp_client.server_manager.close_all_connections()
        del sessions[session_id]
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        del sessions[session_id]  # 即使出错也要删除会话
        return {"message": "Session deleted (with cleanup errors)"}


@router.get("/sessions")
async def list_sessions():
    """列出所有活跃会话"""
    session_info = []
    for session_id, chat_client in sessions.items():
        session_info.append({
            "session_id": session_id,
            "model_name": chat_client.model_name,
            "max_tool_calls": getattr(chat_client, 'max_tool_calls', 5)
        })

    return {"sessions": session_info, "total": len(session_info)}


@router.get("/tools")
async def list_available_tools():
    """列出可用工具（使用临时会话）"""
    try:
        # 创建临时会话来获取工具列表
        base_url = os.environ.get("BASE_URL", "https://api.deepseek.com")
        api_key_env = "OPENAI_API_KEY"

        temp_client = LLMClient(
            model_name="deepseek-chat",
            base_url=base_url,
            api_key_env=api_key_env
        )
        tools = await temp_client.mcp_client.list_tools()
        await temp_client.mcp_client.server_manager.close_all_connections()

        return {"tools": tools, "total": len(tools)}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")