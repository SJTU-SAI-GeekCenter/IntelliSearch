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

## `config/config.yaml` 文件配置

重构后的 `IntelliSearch-v3.1` 采用 [`config/config.yaml`](/config/config.example.yaml) 作为**统一的配置文件**，该文件可通过如下脚本生成：

```bash
# 在当前工作目录下运行：
# 可以检查当前 uv 环境是否正确被激活

bash setup.sh
```

### API 密钥配置

> [!IMPORTANT]
> 下文的配置教程涉及多个 MCP Server，都是可选择的配置。可以在配置文件 `config/config.yaml` 的 `server_choice` 字段自主选择加载 MCP Server 的配置。

- `OPENAI_API_KEY`: 支持 OPENAI-SDK 格式模型调用服务密钥
- `BASE_URL`: 支持 OPENAI-SDK 格式模型调用服务的调用端口
- [`ZHIPU_API_KEY`](https://bigmodel.cn/usercenter/proj-mgmt/apikeys): 中文高质量网页搜索服务密钥
- [`SERPER_API_KEY`](https://serper.dev/dashboard): 谷歌系列的高质量信息源搜索
- [`MEMOS_API_KEY`](https://memos-dashboard.openmem.net/quickstart/): MemOS 外部智能体知识库检索和记忆服务
- [`GITHUB_TOKEN`](https://github.com/settings/tokens): Github 代码搜索，个人鉴权凭证
- [`AMAP_MAPS_API_KEY`](https://lbs.amap.com/api/mcp-server/create-project-and-key): 高德地图 API Key，用于地理信息查询搜索
- [`BILIBILI_SESSDATA`, `BILIBILI_BILI_JCT`, `BILIBILI_BUVID3`](https://nemo2011.github.io/bilibili-api/#/get-credential): Bilibili 鉴权相关凭证
- [`DOUBAN_COOKIE`](https://github.com/yoyooyooo/douban-mcp?tab=readme-ov-file#configuration): Douban 鉴权相关凭证

### 工具后端服务启动

部分 MCP 服务器需要后端服务支持，在使用前需要启动以下服务：

- `backend/tool_backend/rag_service.py` (本地 RAG 搜索服务) 部署在本地 39255 端口
- `backend/tool_backend/ipython_service.py` (IPython 代码执行服务) 部署在本地 39256 端口

```bash
# Start all services
python backend/tool_backend/run.py

# Stop all services
python backend/tool_backend/run.py --stop

# Check service status
python backend/tool_backend/run.py --status

# Restart services
python backend/tool_backend/run.py --stop && python backend/tool_backend/run.py
```

上述文件会自动启动服务到 tmux 中。

### Embedding 模型下载 (Optional)

本仓库使用 RAG 系统来针对自建高质量数据库进行检索，并且分离为 FastAPI 后端服务。因此，在本地部署之前，需要在 `./models` 文件夹下部署 `models/all-MiniLM-L6-v2` 文件夹。下载模型可以通过 [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) 或者 [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2) 进行下载，具体的下载命令详见官网。

> 文件路径也可在 `config/config.yaml` 中修改。


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
python frontend/app.py
```
