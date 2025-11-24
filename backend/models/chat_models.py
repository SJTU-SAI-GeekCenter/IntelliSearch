"""
聊天相关的数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色: system, user, assistant, tool")
    content: str = Field(..., description="消息内容")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用列表")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    use_tools: bool = Field(True, description="是否使用工具")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str = Field(..., description="响应内容")
    session_id: str = Field(..., description="会话ID")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用信息")


class ToolCallInfo(BaseModel):
    """工具调用信息模型"""
    id: str = Field(..., description="工具调用ID")
    name: str = Field(..., description="工具名称")
    arguments: str = Field(..., description="工具参数")


class ToolResult(BaseModel):
    """工具结果模型"""
    id: str = Field(..., description="工具调用ID")
    name: str = Field(..., description="工具名称")
    result: str = Field(..., description="工具执行结果")


class StreamEvent(BaseModel):
    """流式事件模型"""
    type: str = Field(..., description="事件类型: content, tool_call_start, tool_call_delta, tool_result, error")
    content: Optional[str] = Field(None, description="文本内容")
    tool_call: Optional[ToolCallInfo] = Field(None, description="工具调用信息")
    tool_result: Optional[ToolResult] = Field(None, description="工具执行结果")
    error: Optional[str] = Field(None, description="错误信息")


class ChatSession(BaseModel):
    """聊天会话模型"""
    session_id: str = Field(..., description="会话ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息历史")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")