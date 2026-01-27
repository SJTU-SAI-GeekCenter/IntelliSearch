import sys
import os
import logging
import time
import json

from dotenv import load_dotenv

load_dotenv()

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from src.json_vector_store import JSONVectorStoreManager
from mcp.server.fastmcp import FastMCP

sys.path.append(os.getcwd())
from ui.log_config import setup_logging

setup_logging(log_file_path="./log/rag_database.log")
logger = logging.getLogger(__name__)
mcp = FastMCP("local-rag-database")


@mcp.tool()
def local_search(query: str):
    """上海交通大学人工智能学院 (SJTU AI) 本地数据库检索工具

    调用条件: 当用户的提问 (query) 明确涉及上海交通大学人工智能学院 (SJTU AI) 的课程、科研、师资、培养方案、招生、学生生活、政策或其他相关内部知识时，应当调用此工具。
    功能: 在本地知识库中检索与 query 最相关的信息，并生成一个整合的回答 (answer) 和支持此回答的原始文档片段。

    Args:
        query (str): 用户的原始问题或检索请求。例如："SJTU AI 深度学习科研方向有哪些？", "人工智能学院本科生培养方案", "开学迎新礼包包含什么文件"。

    Returns:
        dict: 包含检索结果的字典。
        - "answer" (str): 基于检索到的相关文档生成的摘要性、精简的解答。
        - "related_docs" (list[dict]): 最相关的原始文档片段列表，通常返回 3-5 个最相关的结果。
            - "summary" (str): 原始文档片段的简短摘要或标题。
            - "content" (str): 原始文档片段的全文或关键内容。
            - "meta_info" (dict): 原始文档的元数据，例如来源文件名、URL、章节、页码、创建日期等，用于溯源。

    !!! ATTENTION: 因为我们使用 RAG 进行数据库检索，因此请你尽可能提供较多的关键词进行检索！
    """
    # 初始化（自动加载或创建）
    jsv = JSONVectorStoreManager(
        json_file_path="./document/meta_info.json", persist_directory="./chroma_db_json"
    )
    results = jsv.search(query, score_threshold=0.5)
    return results


def test(query):
    start_time = time.time()
    result = local_search(query=query)
    end_time = time.time()
    print(f"\n\nTesting for query: {query}")
    print(f"Return result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print(f"Time cost: {end_time - start_time}s\n\n")


if __name__ == "__main__":
    # 部署环境需要启动命令，测试环境可以先注释掉
    mcp.run()

    # # 测试可以直接调用函数测试，例如
    # TEST_CASES = [
    #     "上海交通大学体育工作公众号平时会发什么？",
    #     "新学期租赁空调需要多少租金？",
    #     "我们学院上海交通大学第三十六次学生代表大会正式代表及常任代表候选人是谁？",
    # ]
    # for test_case in TEST_CASES:
    #     test(query=test_case)
    
