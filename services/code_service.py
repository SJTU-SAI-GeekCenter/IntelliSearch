"""Code Service for OpenAI-compatible API backend."""

import time
import uuid
from typing import List, Dict, Any

from core.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    ChatCompletionUsage,
)
from core.schema import AgentRequest, AgentResponse
from core.factory import AgentFactory
from core.logger import get_logger


class CodeService:
    """Service layer for Code Backend that bridges OpenAI API format with IntelliSearch agents."""

    def __init__(self, agent_config: Dict[str, Any]):
        self.logger = get_logger(__name__, "code_service")
        self.model_name = agent_config.get("model_name", "intellisearch")

        try:
            agent_type = agent_config.get("type", "mcp_base_agent")
            self.agent = AgentFactory.create_agent(
                agent_type=agent_type,
                name="CodeBackendAgent",
                **{k: v for k, v in agent_config.items() if k != "type"}
            )
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise

        self.tokenizer = None
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.logger.warning("tiktoken not installed, using fallback token estimation")
        except Exception as e:
            self.logger.warning(f"Failed to load tiktoken: {e}, using fallback")

    def _count_tokens(self, text: str) -> int:
        if not text:
            return 0

        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass

        return len(text) // 2

    def _build_context_from_messages(self, messages: List[ChatMessage]) -> str:
        prompt_parts = []

        for msg in messages:
            role = msg.role.upper()
            content = msg.content

            if not content or not content.strip():
                continue

            prompt_parts.append(f"{role}: {content.strip()}")

        return "\n".join(prompt_parts)

    async def process_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        start_time = time.time()

        try:
            prompt = self._build_context_from_messages(request.messages)
            prompt_tokens = self._count_tokens(prompt)

            import nest_asyncio
            nest_asyncio.apply()

            agent_request = AgentRequest(prompt=prompt)
            agent_response: AgentResponse = self.agent.inference(agent_request)

            execution_time = time.time() - start_time
            completion_tokens = self._count_tokens(agent_response.answer)
            total_tokens = prompt_tokens + completion_tokens

            return self._to_openai_format(
                agent_response=agent_response,
                request_model=request.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

        except Exception as e:
            self.logger.error(f"Request processing failed: {e}", exc_info=True)
            raise

    def _to_openai_format(
        self,
        agent_response: AgentResponse,
        request_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> ChatCompletionResponse:
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
            created=int(time.time()),
            model=request_model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=agent_response.answer
                    ),
                    finish_reason="stop" if agent_response.status == "success" else "error"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )

    def get_agent_info(self) -> Dict[str, str]:
        return {
            "name": self.agent.name,
            "type": self.agent.__class__.__name__,
            "model_name": self.model_name,
        }
