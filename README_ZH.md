# IntelliSearch

> [!IMPORTANT]
> 搜索能力的边界就是智能体的边界。

IntelliSearch 是一个基于 MCP (Model Context Protocol) 协议的智能搜索聚合平台，旨在提升智能体的搜索边界能力，让模型能够服务于更复杂的搜索任务。智搜集成了多种 MCP 优质搜索工具，包括：

- 经典强大网页搜索工具 (`Google Search`, `ZHIPU_search`, `web_parse`)
- 地理信息搜索 (Amap MCP Server)
- Bilibili 视频搜索 (Bilibili MCP Server)
- 豆瓣影评搜索 (Douban MCP Server)
- 学术搜索 (Scholar Search Server)
- 12306 火车信息搜索 (12306 MCP Server)
- 微信公众号搜索 (Wechat Search)
- SAI 自建数据库搜索 (SAI Local Search)
- Python 代码执行 (IPython MCP Server)，为智能体提供强大的动态代码执行环境。
- [COMING!] 本地文件操作和执行

## 演示

![CLI Interface Demo](./assets/cli_interface_demo.png)

## 开发者指南

### 环境准备

```bash
# clone the project
git clone https://github.com/xiyuanyang-code/IntelliSearch.git

# install dependency
uv sync
source .venv/bin/activate
```

### 使用前配置

#### API 密钥配置

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

- 模型的 API 密钥和 baseurl，支持 OpenAI SDK Format。
- `ZHIPU_API_KEY` 主要用于中文高质量网页搜索
    - [ZHIPU_OFFICIAL_WEBSITES](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 可以在此处注册模型服务
    - 同时，该密钥也可以用于模型服务
- `SERPER_API_KEY` 主要用于谷歌系列的高质量信息源搜索
    - [SERPER_OFFICIAL_WEBSITES](https://serper.dev/dashboard)，每个初始注册用户有 2500 credits 的免费额度。

#### MCP 服务器配置

为了保证速度和稳定性，所有搜索工具都**采用本地部署**并且使用 stdio 方式进行 MCP 通信。在启动之前需要做如下配置：

1. 复制 MCP 服务器配置文件：

```bash
cp config/config.example.json config/config.json
cp config/config.example.yaml config/config.yaml
```

2. 在 `config/config.json` 中添加相应的 API 密钥和配置：
   - `ZHIPU_API_KEY` 和 `SERPER_API_KEY` 用于 `web_search` 工具
   - `SESSDATA`、`bili_jct` 和 `buvid3` 用于 Bilibili 搜索 ([获取方法](https://github.com/L-Chris/bilibili-mcp))
   - `COOKIE` 用于 `douban_search` ([Douban MCP](https://github.com/moria97/douban-mcp))
   - `AMAP_MAPS_API_KEY` 用于 `amap-mcp-server` ([申请地址](https://lbs.amap.com/api/mcp-server/create-project-and-key))

3. 根据需要修改文件路径配置

> [!IMPORTANT]
> 所有支持 stdio 的 MCP 服务器都可以轻松集成！你可以自由添加自定义工具和 MCP 服务器。

#### SAI 本地搜索配置

本仓库使用 RAG 系统来针对 SAI 自建高质量数据库进行检索，并且分离为 FastAPI 后端服务。因此，在本地部署之前，需要在 `./models` 文件夹下部署 `models/all-MiniLM-L6-v2` 文件夹。下载模型可以通过 [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) 或者 [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2) 进行下载，具体的下载命令详见官网。


#### 后端服务启动

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

### 使用方法

> [!IMPORTANT]
> 在此部分之前，请务必确保已经完成了上述的配置流程。

IntelliSearch 为用户提供了两种使用方式：

- **CLI 使用方式**: 直接在命令行中使用，高效快捷，适合开发者快速测试和添加新功能
- **Web 使用方式**: 使用 FastAPI 框架实现后端模型服务部署，搭配前端网页渲染，适合成品展示和生产环境使用

#### 命令行使用

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

## 项目架构

IntelliSearch 采用了**分层架构**设计，将系统职责清晰分离为以下几层：

- **核心层** (`core/`): 定义抽象基类和数据模型
  - `BaseAgent`: 所有 Agent 的抽象基类
  - `AgentFactory`: Agent 工厂模式实现
  - `AgentRequest`/`AgentResponse`: 统一的请求/响应模型

- **智能体层** (`agents/`): 具体的 Agent 实现
  - `MCPBaseAgent`: 集成 MCP 工具的主 Agent

- **记忆层** (`memory/`): 对话上下文管理
  - `BaseMemory`: 记忆抽象接口
  - `SequentialMemory`: 线性上下文管理实现

- **工具层** (`tools/`): MCP 协议通信
  - `MCPBase`: MCP 工具通信组件
  - `MultiServerManager`: MCP 服务器生命周期管理

- **UI 层** (`ui/`): 统一的用户界面组件
- **API 层** (`backend/`): Web API 接口

这种架构设计使得系统具有高度的可扩展性，你可以轻松地：
- 添加新的 Agent 类型（继承 `BaseAgent`）
- 实现自定义的记忆管理策略（实现 `BaseMemory`）
- 集成新的 MCP 服务器（在 `config/config.json` 中配置）

## Todo List

- [ ] Refactor and Enhance Local SAI Search
    - 实现爬虫管道化
- [x] 更新 README 文档
- [ ] Record Demos
- [ ] 添加更多 MCP 服务器集成