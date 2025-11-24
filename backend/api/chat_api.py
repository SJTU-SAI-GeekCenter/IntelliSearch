"""
聊天API路由
"""
import os
import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from backend.models.chat_models import (
    ChatRequest, ChatResponse, ChatSession, ChatMessage
)
from backend.core.llm_client import LLMClient


# 配置日志
logging.getLogger("mcp").setLevel(logging.CRITICAL)

# 创建路由器
router = APIRouter(prefix="/api/chat", tags=["chat"])

# 存储会话的内存字典
sessions: Dict[str, ChatSession] = {}

# 初始化LLM客户端
try:
    llm_client = LLMClient()
except Exception as e:
    logging.error(f"Failed to initialize LLM client: {e}")
    llm_client = None


def get_or_create_session(session_id: Optional[str] = None) -> ChatSession:
    """获取或创建会话"""
    if session_id and session_id in sessions:
        session = sessions[session_id]
        session.updated_at = datetime.now().isoformat()
        return session

    # 创建新会话
    new_session_id = session_id or str(uuid.uuid4())
    now = datetime.now().isoformat()

    # 添加系统消息
    system_message = ChatMessage(
        role="system",
        content=llm_client.get_system_prompt() if llm_client else "You are a helpful assistant."
    )

    session = ChatSession(
        session_id=new_session_id,
        messages=[system_message],
        created_at=now,
        updated_at=now
    )

    sessions[new_session_id] = session
    return session


def convert_session_to_messages(session: ChatSession) -> List[Dict[str, Any]]:
    """将会话消息转换为LLM客户端格式"""
    messages = []
    for msg in session.messages:
        message_dict = {
            "role": msg.role,
            "content": msg.content
        }
        if msg.tool_call_id:
            message_dict["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls:
            message_dict["tool_calls"] = msg.tool_calls
        messages.append(message_dict)
    return messages


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    if not llm_client:
        raise HTTPException(status_code=500, detail="LLM client not initialized")

    try:
        # 获取或创建会话
        session = get_or_create_session(request.session_id)

        # 添加用户消息
        user_message = ChatMessage(role="user", content=request.message)
        session.messages.append(user_message)

        # 转换消息格式
        messages = convert_session_to_messages(session)

        async def generate_response():
            """生成流式响应"""
            try:
                # 准备工具
                tools = None
                if request.use_tools:
                    tools = await llm_client.mcp_client.list_tools()
                    if not tools:
                        logging.warning("No tools available")

                assistant_content = ""

                # 流式处理
                async for event in llm_client.chat_completion_stream(
                    messages=messages,
                    tools=tools,
                    max_tool_calls=5
                ):
                    # 转换为SSE格式
                    event_json = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_json}\n\n"

                    # 收集助手回复内容
                    if event["type"] == "content":
                        assistant_content += event["content"]

                # 添加助手消息到会话
                if assistant_content:
                    assistant_message = ChatMessage(
                        role="assistant",
                        content=assistant_content
                    )
                    session.messages.append(assistant_message)

                # 发送结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                logging.error(f"Error in stream generation: {e}")
                error_event = {
                    "type": "error",
                    "error": f"Stream generation error: {str(e)}"
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")
    except Exception as e:
        logging.error(f"Error in chat_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """非流式聊天接口"""
    if not llm_client:
        raise HTTPException(status_code=500, detail="LLM client not initialized")

    try:
        # 获取或创建会话
        session = get_or_create_session(request.session_id)

        # 添加用户消息
        user_message = ChatMessage(role="user", content=request.message)
        session.messages.append(user_message)

        # 转换消息格式
        messages = convert_session_to_messages(session)

        # 准备工具
        tools = None
        if request.use_tools:
            tools = await llm_client.mcp_client.list_tools()
            if not tools:
                logging.warning("No tools available")

        # 收集完整响应
        assistant_content = ""
        tool_calls_info = []

        async for event in llm_client.chat_completion_stream(
            messages=messages,
            tools=tools,
            max_tool_calls=5
        ):
            if event["type"] == "content":
                assistant_content += event["content"]
            elif event["type"] == "tool_call_start":
                tool_calls_info.append({
                    "id": event["tool_call"]["id"],
                    "name": event["tool_call"]["name"],
                    "arguments": ""
                })
            elif event["type"] == "tool_call_delta":
                if tool_calls_info:
                    tool_calls_info[-1]["arguments"] += event["tool_call"]["arguments"]

        # 添加助手消息到会话
        if assistant_content:
            assistant_message = ChatMessage(
                role="assistant",
                content=assistant_content,
                tool_calls=tool_calls_info if tool_calls_info else None
            )
            session.messages.append(assistant_message)

        return ChatResponse(
            content=assistant_content,
            session_id=session.session_id,
            tool_calls=tool_calls_info if tool_calls_info else None
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")
    except Exception as e:
        logging.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"message": "Session deleted successfully"}


@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions():
    """列出所有会话"""
    return list(sessions.values())


@router.get("/tools")
async def list_available_tools():
    """列出可用工具"""
    if not llm_client:
        raise HTTPException(status_code=500, detail="LLM client not initialized")

    try:
        tools = await llm_client.mcp_client.list_tools()
        return {"tools": tools}
    except Exception as e:
        logging.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")