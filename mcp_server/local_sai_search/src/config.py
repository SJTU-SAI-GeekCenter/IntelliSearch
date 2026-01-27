import os
import sys
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
# set up logging config


class Config:
    """配置类 - 使用环境变量管理"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self.DOCUMENT_DIR = self.get_env("DOCUMENT_DIR", "./documents")
        self.VECTOR_STORE_DIR = self.get_env("VECTOR_STORE_DIR", "./chroma_db")
        self.CHUNK_SIZE = int(self.get_env("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP = int(self.get_env("CHUNK_OVERLAP", "200"))
        self.EMBEDDING_MODEL = self.get_env(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.LOCAL_MODEL = self.get_env("LOCAL_MODEL", "llama2")
        self.SEARCH_K = int(self.get_env("SEARCH_K", "3"))
        self.validate_config()

    def get_env(self, key, default=None):
        """安全获取环境变量"""
        value = os.getenv(key, default)
        if value is None:
            self.logger.warning(f"环境变量 {key} 未设置，使用默认值: {default}")
        return value

    def validate_config(self):
        """验证必要配置"""
        if not os.path.exists(self.DOCUMENT_DIR):
            os.makedirs(self.DOCUMENT_DIR, exist_ok=True)
            self.logger.debug(f"创建文档目录: {self.DOCUMENT_DIR}")

        if not os.path.exists(self.VECTOR_STORE_DIR):
            os.makedirs(self.VECTOR_STORE_DIR, exist_ok=True)


config = Config()
