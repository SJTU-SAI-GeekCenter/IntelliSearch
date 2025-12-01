from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import logging
import sys

sys.path.append(os.getcwd())

from utils.log_config import setup_logging

setup_logging(log_file_path="./log/rag_database.log")


def get_device(skip=True):
    if skip:
        return "cpu"
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    except ImportError:
        return "cpu"


class VectorStoreManager:

    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory

        # 创建嵌入模型，添加更多的模型参数来避免tokenizer问题
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="./models/all-MiniLM-L6-v2",
            model_kwargs={
                "device": get_device(skip=False),
            },
            encode_kwargs={"normalize_embeddings": True, "batch_size": 1},
        )
        self.vector_store = None
        self.logger = logging.getLogger(__name__)

    def create_vector_store(self, documents):
        """创建向量数据库"""
        try:
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                persist_directory=self.persist_directory,
            )

            self.logger.info(f"向量数据库已创建并保存到 {self.persist_directory}")
            return self.vector_store
        except Exception as e:
            self.logger.error(f"❌ 处理问题时出错: {str(e)}")
            raise e

    def load_existing_vector_store(self):
        """加载已存在的向量数据库"""
        if os.path.exists(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model,
            )
            self.logger.info("已加载现有向量数据库")
            return self.vector_store
        else:
            self.logger.error("未找到现有向量数据库")
            return None

    def get_retriever(
        self,
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5},
    ):
        """获取检索器"""
        if self.vector_store is None:
            self.load_existing_vector_store()

        if self.vector_store is None:
            raise ValueError("向量数据库未初始化，请先创建或加载")

        return self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5},
        )
