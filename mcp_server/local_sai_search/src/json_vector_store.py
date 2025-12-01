import os
import json
import logging
from langchain_core.documents import Document
from src.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class JSONVectorStoreManager:
    def __init__(self, json_file_path: str, persist_directory: str = "./chroma_db_json"):
        """
        初始化 JSON 向量库管理器
        
        Args:
            json_file_path (str): JSON 文件路径，每个条目需包含 'summary' 字段
            persist_directory (str): Chroma 向量库存储目录
        """
        self.json_file_path = json_file_path
        self.persist_directory = persist_directory
        self.vector_store = None
        self._load_or_create()

    def _load_or_create(self):
        """内部方法：加载或创建向量库"""
        if not os.path.exists(self.json_file_path):
            raise FileNotFoundError(f"JSON 文件不存在: {self.json_file_path}")

        # 初始化底层向量库管理器
        vs_manager = VectorStoreManager(persist_directory=self.persist_directory)
        
        # 尝试加载
        self.vector_store = vs_manager.load_existing_vector_store()
        if self.vector_store is not None:
            logger.info("✅ 已加载现有 JSON 向量库")
            return

        # 不存在则创建
        logger.info("向量库不存在，正在从 JSON 创建...")
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []
        for idx, item in enumerate(data):
            if 'summary' in item:
                documents.append(Document(
                    page_content=item['summary'],
                    metadata={'index': idx}
                ))
            else:
                logger.warning(f"条目 {idx} 缺少 'summary' 字段，已跳过")

        if not documents:
            raise ValueError("JSON 中无有效文档可用于创建向量库")

        self.vector_store = vs_manager.create_vector_store(documents)
        logger.info(f"✅ JSON 向量库创建成功，共 {len(documents)} 个文档")

    def search(self, query: str, score_threshold: float = 0.5):
        """
        搜索相关文档（不进行结果去重）
        
        Args:
            query (str): 查询文本
            score_threshold (float): 相似度阈值，范围建议 [0, 1]
        
        Returns:
            List[Dict]: 原始 JSON 条目列表（按检索顺序）
        """
        if self.vector_store is None:
            raise RuntimeError("向量库未初始化")

        # 创建检索器（注意：search_type 是顶层参数）
        retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": score_threshold}
        )
        results = retriever.invoke(query)

        # 读取原始 JSON
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        # 按检索结果顺序返回原始 JSON 对象（允许重复）
        search_results = []
        for doc in results:
            idx = doc.metadata.get('index')
            if isinstance(idx, int) and 0 <= idx < len(original_data):
                search_results.append(original_data[idx])
            else:
                logger.warning(f"无效索引: {idx}")
        
        return search_results
