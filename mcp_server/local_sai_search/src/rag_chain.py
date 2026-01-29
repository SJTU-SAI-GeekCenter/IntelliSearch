import time
import logging
import os
import sys

sys.path.append(os.getcwd())

from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


class RAGSystem:
    def __init__(self, model_type="openai", vector_store=None, base_url=None):
        """
        初始化RAG系统
        """
        self.model_type = model_type
        self.vector_store: Chroma = vector_store
        self.base_url = base_url
        self.llm = self._initialize_llm()
        self.retriever = None
        self.chain = None
        self.logger = logging.getLogger(__name__)
        self._create_rag_chain()

    def _initialize_llm(self):
        """初始化语言模型"""
        if self.model_type == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("未设置OPENAI_API_KEY环境变量")

            llm_kwargs = {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.3,
                "max_tokens": 500,
                "timeout": 30,
                "max_retries": 2,
            }

            return ChatOpenAI(**llm_kwargs)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def _create_rag_chain(self):
        """创建RAG链，带时间测量"""
        if self.vector_store is None:
            raise ValueError("未提供向量存储实例")
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5}
        )
        # 使用 ChatPromptTemplate
        template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一个有用的AI助手。请根据提供的上下文信息回答问题。
        
请遵循以下规则：
1. 严格基于上下文信息提供准确、简洁的回答
2. 如果上下文信息不足以回答问题，请如实说明
3. 保持回答的专业性和友好性""",
                ),
                (
                    "human",
                    """上下文信息：
{context}

问题：{question}

请根据上下文回答上述问题。""",
                ),
            ]
        )

        def format_docs(docs):
            """格式化检索到的文档"""
            return "\n\n".join(
                f"Document {i+1}: {doc.page_content[:300]}..." 
                for i, doc in enumerate(docs)
            )

        # 创建RAG链
        self.chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | template
            | self.llm
            | StrOutputParser()
        )

    def query(self, question, timeout=60):
        """
        查询方法，带详细时间测量
        """
        self.logger.info(f"开始处理问题: '{question}'")
        start_time = time.time()

        try:
            # 步骤1: 检索相关文档
            self.logger.info("   步骤1: 检索相关文档...")
            retrieval_start = time.time()
            relevant_docs = self.retriever.invoke(question)
            retrieval_time = time.time() - retrieval_start
            self.logger.info(
                f"   检索完成，耗时: {retrieval_time:.2f}秒，找到 {len(relevant_docs)} 个文档"
            )

            # 检查是否超时
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError("检索超时")

            # 步骤2: 生成答案
            self.logger.info("   步骤2: 生成答案...")
            generation_start = time.time()

            # 直接调用链
            answer = self.chain.invoke(question)

            generation_time = time.time() - generation_start
            self.logger.info(f"   答案生成完成，耗时: {generation_time:.2f}秒")

            total_time = time.time() - start_time
            self.logger.info(f"总查询耗时: {total_time:.2f}秒")

            return {
                "answer": answer,
                "source_documents": relevant_docs,
                "timing": {
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "total_time": total_time,
                },
            }
        except TimeoutError as e:
            self.logger.error(f"查询超时: {str(e)}")
            return {
                "answer": "查询超时，请稍后重试。",
                "source_documents": [],
                "timing": {"error": "timeout"},
            }
        except Exception as e:
            self.logger.error(f"查询过程中出错: {str(e)}")
            return {
                "answer": f"处理问题时出错: {str(e)}",
                "source_documents": [],
                "timing": {"error": str(e)},
            }


    def quick_search(self, question):
        """快速检索，不生成答案，用于测试"""
        self.logger.info(f"快速检索测试: '{question}'")
        start_time = time.time()

        try:
            results = self.retriever.invoke(question)
            search_time = time.time() - start_time
            self.logger.info(f"快速检索完成，耗时: {search_time:.2f}秒")
            self.logger.info(f"找到 {len(results)} 个结果")

            for i, doc in enumerate(results):
                self.logger.info(f"结果 {i+1} 预览: {doc.page_content[:100]}...")

            return results
        except Exception as e:
            self.logger.error(f"快速检索失败: {str(e)}")
            return []
