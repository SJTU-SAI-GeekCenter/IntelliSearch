# IntelliSearch-v3.0 开发者使用指南

IntelliSearch-v3.0 全栈框架开源，并提供 **命令行类 Claude Code 使用**模式和**网页端**使用模式两种方式。

## 环境准备

```bash
# clone the project
git clone git@github.com:SJTU-SAI-GeekCenter/IntelliSearch.git

# install dependency
# Python 3.13.5 and uv is recommended
uv sync
source .venv/bin/activate
```

我们使用 [uv](https://docs.astral.sh/uv/) 来管理 Python 版本和环境依赖问题。

> [!IMPORTANT]
> 即将重构 config 部分的代码组件，形成一体化、人类可读的配置文件！

## API 密钥配置

创建 `.env` 文件并写入如下的环境变量：

```bash
# OPENAI_API_KEY 支持 OpenAI SDK 模式
OPENAI_API_KEY=your-api-key
BASE_URL=your-base-url

# ZHIPU_API_KEY 支持网页搜索
ZHIPU_API_KEY=your-api-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# SERPER_API_KEY 网页搜索等一系列工具
SERPER_API_KEY=your-api-key

# MEMOS_API_KEY 支持 MEMOS 的文件搜索
MEMOS_API_KEY="your-memos-api-key"
MEMOS_BASE_URL="https://memos.memtensor.cn/api/openmem/v1"
```

为了保证智能体对话及搜索功能的正常执行，需要设置如下的 API 密钥：

- `OPENAI_API_KEY` & `BASE_URL`: 支持 OpenAI-SDK 格式的模型调用服务（非流式）
- `ZHIPU_API_KEY` (Optional for tools): 中文高质量网页搜索服务
    - [ZHIPU_OFFICIAL_WEBSITES](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 可以在此处注册模型服务
    - 同时，该密钥也可以用于上述模型服务
- `SERPER_API_KEY` (Optional for tools): 谷歌系列的高质量信息源搜索
    - [SERPER_OFFICIAL_WEBSITES](https://serper.dev/dashboard)
- `MEMOS_API_KEY` & `MEMOS_BASE_URL` (Optional for tools): 外部智能体知识库检索和记忆服务
    - [MEMOS_OFFICIAL_WEBSITE](https://memos-dashboard.openmem.net/quickstart/)

## 工具配置

> [!IMPORTANT]
> 所有支持 stdio 的 MCP 服务器都可以轻松集成！你可以自由添加自定义工具和 MCP 服务器。

```bash
cp config/config.example.json config/config.json
cp config/config.example.yaml config/config.yaml
```

在 `config/config.json` 中添加相应的 API 密钥和字段：
- `ZHIPU_API_KEY` 和 `SERPER_API_KEY` 用于 `web_search` 工具
- `SESSDATA`、`bili_jct` 和 `buvid3` 用于 Bilibili 搜索 ([获取方法](https://github.com/L-Chris/bilibili-mcp))
- `COOKIE` 用于 `douban_search` ([Douban MCP](https://github.com/moria97/douban-mcp))
- `AMAP_MAPS_API_KEY` 用于 `amap-mcp-server` ([申请地址](https://lbs.amap.com/api/mcp-server/create-project-and-key))

根据实际的本地路径配置相关路径（建议使用绝对路径）

### SAI 本地搜索配置 (Optional)

本仓库使用 RAG 系统来针对 SAI 自建高质量数据库进行检索，并且分离为 FastAPI 后端服务。因此，在本地部署之前，需要在 `./models` 文件夹下部署 `models/all-MiniLM-L6-v2` 文件夹。下载模型可以通过 [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) 或者 [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2) 进行下载，具体的下载命令详见官网。


### 后端服务启动 (Optional)

部分 MCP 服务器需要后端服务支持，在使用前需要启动以下服务：

- `local_sai` (SAI 本地 RAG 搜索服务) 部署在本地 39255 端口
- `ipython_backend` (Python 代码执行服务) 部署在本地 39256 端口

```bash
# 启动后端服务（会自动检测并清除占用端口）
bash start_backend.sh

# 检查服务状态
bash start_backend.sh status

# 停止服务
bash start_backend.sh stop
```

## 命令行使用

模仿 Claude Code 风格界面设计，在命令行窗口实现简单高效并且可视化的搜索智能体。

![CLI Interface Demo](/assets/cli_interface_demo.png)

```bash
python cli.py
```

#### Web 使用

> [!IMPORTANT]
> 该部分正在重构中，暂时不可用。

IntelliSearch 支持本地 Web 部署，使用 FastAPI 作为后端提供标准化的流式输出接口：

```bash
# 终端 1：启动 FastAPI 后端服务（默认端口 8001）
python backend/main_fastapi.py

# 终端 2：启动 Flask 前端服务（默认端口 50001）
python frontend/flask/app.py
```
