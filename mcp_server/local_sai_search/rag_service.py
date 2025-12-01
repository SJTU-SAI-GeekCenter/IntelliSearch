import os
import sys
import logging
import uvicorn

sys.path.append(os.getcwd())


from src.json_vector_store import JSONVectorStoreManager
from utils.log_config import setup_logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

setup_logging(log_file_path="./log/rag_service.log")
logger = logging.getLogger("RAG_Service")
global_jsv = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_jsv
    logger.info("🚀 [RAG Service] 正在启动，开始预加载向量数据库和模型...")

    try:
        global_jsv = JSONVectorStoreManager(
            json_file_path="./document/meta_info.json",
            persist_directory="./chroma_db_json",
        )
        logger.info("✅ [RAG Service] 数据库加载完成，模型已就绪！")
    except Exception as e:
        logger.error(f"❌ [RAG Service] 初始化失败: {e}")
        raise e

    yield

    logger.info("📴 [RAG Service] 服务关闭，清理资源...")
    global_jsv = None


app = FastAPI(title="SJTU AI RAG Service", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    score_threshold: float = 0.5


@app.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    接收查询请求，使用内存中的 global_jsv 进行检索
    """
    if global_jsv is None:
        raise HTTPException(status_code=500, detail="向量数据库未初始化")

    try:
        results = global_jsv.search(
            query=request.query, score_threshold=request.score_threshold
        )
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"检索出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=23225)
