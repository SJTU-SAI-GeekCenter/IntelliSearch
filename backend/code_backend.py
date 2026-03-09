"""FastAPI backend for OpenAI-compatible Code API."""

import time
import uvicorn
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from core.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelsResponse,
    ModelInfo,
)
from services.code_service import CodeService
from core.logger import get_logger

security = HTTPBearer(auto_error=False)


class CodeBackend:
    """FastAPI backend for OpenAI-compatible Code API."""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__, "code_backend")

        agent_config = config.get("agent", {})
        self.valid_keys: List[str] = config.get("api_keys", [])
        self.require_api_key: bool = config.get("require_api_key", True)

        self.app = FastAPI(
            title="IntelliSearch Code API",
            description="OpenAI-compatible API for IntelliSearch agents",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        try:
            self.service = CodeService(agent_config=agent_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeService: {e}", exc_info=True)
            raise

        self._setup_cors()
        self._setup_routes()

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def verify_api_key(
        self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[str]:
        if not self.require_api_key:
            return None

        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide 'Authorization: Bearer YOUR_KEY'",
            )

        api_key = credentials.credentials
        if not self.valid_keys or api_key not in self.valid_keys:
            self.logger.warning(f"Invalid API key attempt: {api_key[:8]}***")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        return api_key

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            agent_info = self.service.get_agent_info()
            return {
                "service": "IntelliSearch Code API",
                "version": "1.0.0",
                "agent": agent_info,
                "docs": "/docs",
            }

        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}

        @self.app.post(
            "/v1/chat/completions",
            response_model=ChatCompletionResponse,
            dependencies=[Depends(self.verify_api_key)],
        )
        async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
            try:
                return await self.service.process_request(request)
            except RuntimeError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e),
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

        @self.app.get(
            "/v1/models",
            response_model=ModelsResponse,
            dependencies=[Depends(self.verify_api_key)],
        )
        async def list_models() -> ModelsResponse:
            agent_info = self.service.get_agent_info()
            model_name = agent_info.get("model_name", "intellisearch")

            model = ModelInfo(
                id=model_name,
                created=int(time.time()),
                owned_by="intellisearch",
            )
            return ModelsResponse(object="list", data=[model])

        @self.app.get("/v1")
        async def v1_root():
            return {"message": "IntelliSearch Code API v1"}

    def run(self, host: str = "0.0.0.0", port: int = 8002, log_level: str = "info"):
        uvicorn.run(self.app, host=host, port=port, log_level=log_level)
