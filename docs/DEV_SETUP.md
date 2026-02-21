# IntelliSearch-v3.1 开发者使用指南

IntelliSearch-v3.1 全栈框架开源，并提供 **命令行类 Claude Code 使用**模式和**网页端**使用模式两种方式。

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

重构后的 `IntelliSearch-v3.1` 采用 [`config/config.yaml`](https://github.com/SJTU-SAI-GeekCenter/IntelliSearch/blob/main/config/config.example.yaml) 作为**统一的配置文件**，该文件可通过如下脚本生成：

```bash
# 在当前工作目录下运行：
bash setup.sh

# 可以检查当前 uv 环境是否正确被激活
# 该脚本将会自动转化绝对路径并根据 config/config.example.yaml 来生成 config/config.yaml
```

## Model Settings

- `OPENAI_API_KEY`: 支持 OPENAI-SDK 格式模型调用服务密钥
- `BASE_URL`: 支持 OPENAI-SDK 格式模型调用服务的调用端口

对应的密钥填写在 `config/config.yaml` 的 `env` 字段中:

```yaml
env:
  OPENAI_API_KEY: your-api-key
  BASE_URL: "https://api.deepseek.com" # or your own
```

模型名称，智能体类型等内容也可以在 yaml 文件中个性化设置:

```yaml
agent:
  # Agent type to use
  # Override with: AGENT_TYPE
  type: mcp_async_agent

  # Agent display name
  # Override with: AGENT_NAME
  name: IntelliSearchAgent

  # LLM model name
  # Override with: AGENT_MODEL_NAME
  model_name: deepseek-chat

  # Maximum number of tool calls per inference
  # Override with: AGENT_MAX_TOOL_CALL
  max_tool_call: 20

  # Path to MCP server configuration file
  # Override with: AGENT_SERVER_CONFIG_PATH
  server_config_path: config/config.yaml

  # agent system prompt path
  system_prompt_path: prompts/sys_zh.md
```

## Tools Settings

- [IntelliSearch Toolkit Settings](#intellisearch-toolkit-settings): 配置基础的 IntelliSearch Toolkit Settings
- [Tool Backend Service](#tool-backend-service): 启动工具后端服务
- [Tool Selections](#tool-selections-and-additions): 支持**个性化工具搭配和选择**，支持**MCP风格的个性化 Server 和工具导入**
- [Tool Testing](#tool-testing)

### IntelliSearch Toolkit Settings

| 工具名称 | 类型 (Search/Operate) | 基本介绍 | 配置 |
| --- | --- | --- | --- |
| `search_web` | Search | 通用 Web 搜索引擎 (Google, ZHIPU) | ⚠️ Need `ZHIPU_API_KEY` & `SERPER_API_KEY` |
| `search_github` | Search | 搜索 Github 代码库、源码、用户、Issue 及 PR | ⚠️ Need `GITHUB_TOKEN` |
| `search_scholar` | Search | 检索学术论文及文献 (Google Scholar, DBLP, Arxiv) | ⚠️ Need `SERPER_API_KEY` |
| `search_geo` | Search | 地理信息查询、路径规划、POI 搜索及地理编码 | ⚠️ Need `AMAP_MAPS_API_KEY` |
| `search_movie` | Search | 搜索视频内容、电影、图书信息及用户评论 | ⚠️ Need `DOUBAN_COOKIE` |
| `search_train` | Search | 实时 12306 火车票务及列车班次信息查询 | ✅ Tools Available without configurations |
| `search_bilibili` | Search | Bilibili 视频平台内容和字幕信息检索 | ⚠️ Need `BILIBILI_SESSDATA`, `BILIBILI_BILI_JCT`, `BILIBILI_BUVID3` |
| `search_wechat` | Search | 检索微信公众号相关推文 | ✅ Tools Available without configurations |
| `search_local` | Search | 支持 PDF、TXT、MD、DOCX 等本地文件的知识库检索 | ⚠️ Need Embedding Models Downloads |
| `search_sai` | Search | SAI 专属的云端 MemOS 记忆系统 | ⚠️ Need `MEMOS_API_KEY`, `MEMOS_USER_ID` |
| `operate_browser` | Operate | 自动化网页导航、模拟交互及动态内容提取 | ✅ Tools Available without configurations |
| `operate_file` | Operate | 文件操作：对 CSV、PDF、JSON 等文件的创建、读写与管理 | ✅ Tools Available without configurations |
| `operate_python` | Operate | 基于 IPython 的代码运行，支持状态持久化与计算 | ✅ Tools Available without configurations |
| `operate_terminal` | Operate | 执行系统命令，具备超时控制与输出捕获功能 | ✅ Tools Available without configurations |
| `base_toolkit` | Operate | 日期时间、UUID 生成、随机数等原子化实用工具 | ✅ Tools Available without configurations |

- [`ZHIPU_API_KEY`](https://bigmodel.cn/usercenter/proj-mgmt/apikeys): 中文高质量网页搜索服务密钥
- [`SERPER_API_KEY`](https://serper.dev/dashboard): 谷歌系列的高质量信息源搜索
- [`MEMOS_API_KEY`](https://memos-dashboard.openmem.net/quickstart/): MemOS 外部智能体知识库检索和记忆服务
- [`GITHUB_TOKEN`](https://github.com/settings/tokens): Github 代码搜索，个人鉴权凭证
- [`AMAP_MAPS_API_KEY`](https://lbs.amap.com/api/mcp-server/create-project-and-key): 高德地图 API Key，用于地理信息查询搜索
- [`BILIBILI_SESSDATA`, `BILIBILI_BILI_JCT`, `BILIBILI_BUVID3`](https://nemo2011.github.io/bilibili-api/#/get-credential): Bilibili 鉴权相关凭证
- [`DOUBAN_COOKIE`](https://github.com/yoyooyooo/douban-mcp?tab=readme-ov-file#configuration): Douban 鉴权相关凭证
- **Embedding Models**: 本仓库使用 RAG 系统来针对自建高质量数据库进行检索，并且分离为 FastAPI 后端服务。因此，在本地部署之前，需要在 `./models` 文件夹下部署 `models/all-MiniLM-L6-v2` 文件夹。下载模型可以通过 [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) 或者 [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2) 进行下载，具体的下载命令详见官网。(文件路径也可在 `config/config.yaml` 中的 `rag` 字段下进行修改。)

### Tool Backend Service

部分 MCP 服务器需要后端服务支持，如下部分如有需要在使用前需要启动以下服务：

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

### Tool Selections and Additions

IntelliSearch 支持在 `config/config.yaml` 中自定义个性化工具的添加和工具的动态导入：

- 在 `all_servers` 字段集成了**所有 MCP 工具**的导入脚本，支持标准化的 MCP 工具的导入。
- 在 `server_choice` 字段中可以动态导入 MCP 工具，不用导入的注释掉即可。

```yaml
all_servers:
  base_toolkit:
    command: python
    args: <YOUR_PWD>/mcp_server/base_toolkit/server.py
    description: Base Toolkit for Agents providing fundamental tools and utilities

  operate_browser:
    command: python
    args: <YOUR_PWD>/mcp_server/operate_browser/server.py
    description: Browser automation tools using Playwright for web navigation, page interaction, and content extraction

  operate_file:
    command: python
    args: <YOUR_PWD>/mcp_server/operate_file/server.py
    description: Local file system operations including create, read, write, delete, and specialized handling for CSV, PDF, and JSON files

  operate_python:
    command: python
    args: <YOUR_PWD>/mcp_server/operate_python/server.py
    description: Python code execution environment using IPython backend with state persistence and result capture (requires backend service on port 39256)
# ...
```

```yaml
server_choice:
  - base_toolkit
  - operate_browser
  - operate_file
  - operate_python
  - operate_terminal
  - search_bilibili
  - search_geo
  - search_github
#   - search_local
#   - search_movie
#   - search_sai
  - search_scholar
  - search_train 
  - search_web
  - search_wechat_official_account
```

### Tool Testing

为保证工具的可用性，该项目集成了 `pytest` 框架实现工具的模拟测试组件，具体文档和使用说明见: [`PYTEST_README`](https://github.com/SJTU-SAI-GeekCenter/IntelliSearch/blob/main/test/README.md)

## Usage

### CLI Service

模仿 Claude Code 风格界面设计，在命令行窗口实现简单高效并且可视化的搜索智能体。

![CLI Interface Demo](./assets/cli_interface_demo.png)

```bash
python cli.py
```

### Web Service

IntelliSearch 支持本地 Web 部署，使用 FastAPI 作为后端提供标准化的流式输出接口

![Web Interface Demo](./assets/web_interface_demo.png)

```bash
python api.py
# 前端服务：本地 50001 端口
# 后端服务：本地 8001 端口
# 后端 API 文档：http://localhost:8001/docs
python api.py
```
