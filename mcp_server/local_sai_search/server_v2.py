# server.py
import os
import sys
import logging
import httpx
import asyncio
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 加载环境变量 (如果 FastMCP 需要 key)
load_dotenv()

sys.path.append(os.getcwd())
from utils.log_config import setup_logging

setup_logging(log_file_path="./log/mcp_server.log")
logger = logging.getLogger("MCP_Server")
mcp = FastMCP("local-rag-database")
PORT = 23225
RAG_SERVICE_URL = f"http://127.0.0.1:{PORT}/search"


@mcp.tool()
async def local_search(query: str):
    """上海交通大学人工智能学院 (SJTU AI) 本地数据库检索工具

    调用条件: 当用户的提问 (query) 明确涉及上海交通大学人工智能学院 (SJTU AI) 的课程、科研、师资、培养方案、招生、学生生活、政策或其他相关内部知识时，应当调用此工具。
    功能: 在本地知识库中检索与 query 最相关的信息。

    Args:
        query (str): 用户的原始问题或检索请求。

    Returns:
        dict: 检索结果列表。
    """
    logger.info(f"收到 MCP 查询请求: {query}，正在转发给 RAG Service...")

    # 构造请求数据
    payload = {"query": query, "score_threshold": 0.3}

    try:
        # 使用异步 HTTP 客户端调用本地的 8000 端口服务
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RAG_SERVICE_URL,
                json=payload,
                timeout=30.0,  # 设置超时时间，防止模型算太久
            )

            # 检查 HTTP 状态码
            response.raise_for_status()

            # 获取返回数据
            data = response.json()

            if data.get("status") == "success":
                results = data.get("results")
                logger.info(f"RAG Service 返回了 {len(results)} 条结果")
                # 直接返回给 LLM，或者在这里做进一步格式化
                return results
            else:
                return f"RAG Service 内部错误: {data}"

    except httpx.ConnectError:
        error_msg = "❌ 无法连接到 RAG Service。请检查 rag_service.py 是否已启动。"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"调用 RAG Service 时发生错误: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def simple_test(query: str):
    result = await local_search(query=query)
    print(result)


if __name__ == "__main__":
    # mcp.run()
    asyncio.run(simple_test("空调"))
