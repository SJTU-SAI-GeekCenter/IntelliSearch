import os
import sys
import logging
sys.path.append(os.getcwd())

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.logger = logging.getLogger(__name__)

    def load_document(self, file_path):
        """加载文档，支持PDF和TXT格式"""
        if file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        elif (
            file_path.endswith(".md")
            or file_path.endswith(".txt")
            # or file_path.endswith(".json")
        ):
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError("不支持的文件格式，仅支持PDF和TXT")

        documents = loader.load()
        return documents

    def split_documents(self, documents):
        """将文档分割成小块"""
        return self.text_splitter.split_documents(documents)
 

    def process_directory(self, directory_path):
        """
        递归处理整个目录及其子目录下的文档。
        支持的文件类型：.pdf, .txt, .json, .md。
        """
        all_docs = []
        supported_extensions = (".pdf", ".txt", ".json", ".md")

        # os.walk 迭代地生成目录树中的文件名
        for root, _, files in os.walk(directory_path):
            for filename in files:
                # 检查文件扩展名
                if filename.lower().endswith(supported_extensions):
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, directory_path) # 用于日志记录
                    
                    try:
                        # self.load_document 负责加载文档并返回 Document 对象列表
                        docs = self.load_document(file_path)
                        all_docs.extend(docs)
                        # 使用相对路径，日志更清晰
                        self.logger.info(f"成功加载文档: {relative_path}")
                    except Exception as e:
                        self.logger.error(f"加载文档 {relative_path} 时出错: {str(e)}")

        if not all_docs:
            raise ValueError(f"未找到可处理的文档 (支持类型: {', '.join(supported_extensions)})")

        # self.split_documents 负责将加载的文档切分成块
        split_docs = self.split_documents(all_docs)
        self.logger.info(f"文档处理完成，共生成 {len(split_docs)} 个文本块")
        return split_docs
