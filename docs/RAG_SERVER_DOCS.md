# RAG Backend Service

基于 txtai 的高性能文档检索服务,支持多种文件格式的语义搜索。

## 功能特性

- **多格式支持**: PDF, TXT, MD, DOCX 等多种文件格式
- **智能分块**: 自动文本分割,支持自定义块大小和重叠
- **语义搜索**: 基于向量相似度的语义检索
- **增量更新**: 支持添加和删除文档
- **持久化存储**: 向量索引持久化到磁盘
- **RESTful API**: 提供 FastAPI HTTP 接口

## 架构设计

```
rag_src/
├── __init__.py          # 统一导出接口
├── core.py              # 核心 RAG 引擎
├── embeddings.py        # 向量存储和检索封装
├── documents.py         # 文档处理和索引管理
├── server.py            # FastAPI 服务
└── README.md            # 本文档
```

### 核心组件

#### 1. EmbeddingManager (embeddings.py)
封装 txtai 的 Embeddings 类,提供:
- 向量索引的创建、加载、保存
- 文档搜索(upsert, delete)
- 相似度检索(search)

#### 2. DocumentProcessor (documents.py)
使用 txtai 的 Textractor 处理文档:
- 多格式文本提取
- 智能分块(chunking)
- 批量目录处理

#### 3. RAGService (core.py)
核心 RAG 引擎,集成上述组件:
- 文档索引管理
- 检索接口
- 统计信息

#### 4. FastAPI Server (server.py)
HTTP 服务,提供 RESTful API

## 配置说明

所有配置都在 `config/config.yaml` 的 `rag` 节点:

```yaml
rag:
  # Embedding 模型配置
  embedding:
    model_path: "./models/all-MiniLM-L6-v2"
    device: "cpu"  # cpu, mps, cuda

  # 向量索引配置
  index:
    path: "./data/rag_index"
    content: true

  # 文档处理配置
  documents:
    chunk_size: 500
    overlap: 50
    supported_formats: ["pdf", "txt", "md", "docx"]

  # 检索配置
  search:
    default_limit: 5
    score_threshold: 0.7

  # 自动初始化配置 (可选)
  initialization:
    load_dir: "/path/to/documents"  # 启动时自动索引此目录
```

### 环境变量覆盖

配置可通过环境变量覆盖(格式: `RAG_<SECTION>_<KEY>`):

```bash
export RAG_EMBEDDING_MODEL_PATH="./models/my-model"
export RAG_INDEX_PATH="./data/custom_index"
export RAG_SEARCH_DEFAULT_LIMIT=10
```

## 快速开始

### 1. 安装依赖

```bash
pip install txtai fastapi uvicorn
```

### 2. 下载模型

```bash
# 创建模型目录
mkdir -p models

# 下载 sentence-transformers 模型
# 方式1: 使用 git clone
git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 models/all-MiniLM-L6-v2

# 方式2: 使用 HuggingFace API (首次运行自动下载)
# txtai 会自动下载模型到指定路径
```

### 3. 准备文档

```bash
mkdir -p documents
# 将你的 PDF, TXT, MD 等文件放入 documents 目录
```

### 4. 启动服务

```bash
# 直接运行 rag_service.py
python backend/tool_backend/rag_service.py
```

服务默认运行在 `http://0.0.0.0:39257`

**自动初始化功能**:

如果在 `config.yaml` 中配置了 `rag.initialization.load_dir`,服务启动时会自动索引指定目录的所有文档:

```yaml
rag:
  initialization:
    load_dir: "/Users/xiyuanyang/Desktop/Dev/IntelliSearch-v2/data/RAG"
```

启动时日志会显示:
```
[RAG Service] Auto-indexing directory: /path/to/documents
[RAG Service] Auto-indexing completed: 150 chunks
```

这样可以实现"开箱即用"的体验,无需手动调用索引 API。

## API 使用示例

### 1. 索引文档

#### 索引单个文件
```bash
curl -X POST "http://localhost:39257/index/file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./documents/sample.pdf",
    "save": true
  }'
```

#### 索引整个目录
```bash
curl -X POST "http://localhost:39257/index/directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./documents",
    "recursive": true,
    "save": true
  }'
```

### 2. 搜索文档

```bash
curl -X POST "http://localhost:39257/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是机器学习?",
    "limit": 5,
    "threshold": 0.7
  }'
```

响应示例:
```json
{
  "status": "success",
  "query": "什么是机器学习?",
  "results": [
    {
      "id": "doc1_chunk0",
      "score": 0.89,
      "text": "机器学习是人工智能的一个分支..."
    }
  ],
  "count": 1
}
```

### 3. 删除文档

```bash
curl -X DELETE "http://localhost:39257/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc1", "doc2"],
    "save": true
  }'
```

### 4. 服务状态

```bash
curl "http://localhost:39257/status"
```

响应:
```json
{
  "status": "success",
  "index_exists": true,
  "index_path": "./data/rag_index",
  "supported_formats": ["pdf", "txt", "md", "docx"]
}
```

### 5. 手动保存/加载索引

```bash
# 保存索引
curl -X POST "http://localhost:39257/index/save"

# 加载索引
curl -X POST "http://localhost:39257/index/load"
```