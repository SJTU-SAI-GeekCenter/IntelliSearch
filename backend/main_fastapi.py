"""
FastAPI主应用文件
"""
import os
import logging
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 添加当前目录到Python路径
sys.path.append(os.getcwd())

# 导入环境配置
import dotenv

# 导入日志配置
from utils.log_config import setup_logging

# 导入API路由
from backend.api.chat_api import router as chat_router

# 加载环境变量
dotenv.load_dotenv()

# 设置日志
setup_logging(log_file_path="./log/fastapi.log", project_prefix="IntelliSearch FastAPI")

# 设置MCP日志级别
logging.getLogger("mcp").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Starting up FastAPI application...")
    yield
    logger.info("📴 Shutting down FastAPI application...")


# 创建FastAPI应用实例
app = FastAPI(
    title="IntelliSearch API",
    description="智能搜索聊天机器人API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "IntelliSearch API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """根路径重定向到前端"""
    return {"message": "Welcome to IntelliSearch API. Access /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn

    logger.info("🌟 Starting IntelliSearch FastAPI server...")

    uvicorn.run(
        "backend.main_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )