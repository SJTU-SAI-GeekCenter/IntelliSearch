<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=900&size=50&pause=50&color=000000&center=true&vCenter=true&width=600&height=80&lines=IntelliSearch" alt="Typing SVG" />
  </a>
</div>

# IntelliSearch

> [!IMPORTANT]
> The boundaries of searching capabilities are the boundaries of agents.

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

## 演示

> [!NOTE]
> 将在未来版本中发布。

## 开发者指南

> [!NOTE]
> 下面为开发者提供了极简的开发和复现指南，欢迎 PR！

如有任何问题，请联系 [yangxiyuan@sjtu.edu.cn](mailto:yangxiyuan@sjtu.edu.cn)！

### 环境准备

```bash
# clone the project
git clone https://github.com/xiyuanyang-code/IntelliSearch.git

# 初始化子模块
git submodule init

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
```

为了保证智能体对话及搜索功能的正常执行，需要设置如下的 API 密钥：

- 模型的 API 密钥和 baseurl，支持 OpenAI SDK Format。
- `ZHIPU_API_KEY` 主要用于中文高质量网页搜索
    - [ZHIPU_OFFICIAL_WEBSITES](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 可以在此处注册模型服务
    - 同时，该密钥也可以用于模型服务
- `SERPER_API_KEY` 主要用于谷歌系列的高质量信息源搜索
    - [SERPER_OFFICIAL_WEBSITES](https://serper.dev/dashboard)，每个初始注册用户有 2500 credits 的免费额度。

#### MCP 服务器配置

为了保证速度和稳定性，用到的搜索工具都**采用本地部署**并且使用 stdio 的方式作为 MCP 的通信方式。在启动 MCP Server 之前需要做如下配置：

- Copy `config.json` from `config.example.json`:
    - See [Config Example](./config.example.json) for more details
- Add several api-keys and settings
    - `ZHIPU_API_KEY` and `SERPER_API_KEY` for `web_search` tools.
    - `SESSDATA`, `bili_jct` and `buvid3` for Bilibili Search tools. ([Bilibili MCP](https://github.com/L-Chris/bilibili-mcp))
    - `COKKIE` for `douban_search` ([Douban MCP](https://github.com/moria97/douban-mcp))
    - `AMAP_MAPS_API_KEY` for `amap-mcp-server`. ([Amap MCP Server](https://lbs.amap.com/api/mcp-server/create-project-and-key))
- Change the file path

> [!IMPORTANT]
> All stdio mcp servers are supported! You can easily add your custom tools and mcp servers yourself.

#### SAI 本地搜索配置

本仓库使用 RAG 系统来针对 SAI 自建高质量数据库进行检索，并且分离为 FastAPI 后端服务。因此，在本地部署之前，需要在 `./models` 文件夹下部署 `models/all-MiniLM-L6-v2` 文件夹。下载模型可以通过 [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) 或者 [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2) 进行下载，具体的下载命令详见官网。


#### 后端服务启动

在 MCP Server 中，`ipython-mcp` 和 `sai-local-search` 是需要后端服务通信的，因此需要在使用之前启动后端服务：

- `ipython-mcp` 部署在本地 39255 端口
- `local_sai_search` 部署在本地 39256 端口

```bash
# 清除对应端口并且启动服务
bash scripts/backend.sh

# 检查当前的服务状态
bash scripts/backend.sh status

# 终止服务
bash scripts/backend.sh stop
```

### 使用方法

> [!IMPORTANT]
> 在此部分之前，请务必确保已经完成了上述的配置流程。

智搜项目为用户提供了两种使用方式：

- **CLI 使用方式**: 直接在命令行中使用，高效快捷，方便开发者开发新功能
- **网页使用方式**: 使用 FastAPI 框架实现后端模型服务部署，同时搭配前端网页渲染，适合成品展示和生产环境中用户使用。

#### 命令行使用

```bash
python backend/cli_v2.py
# 支持流式输出
```

#### 网页使用

智搜项目也支持网页端的本地部署，后端使用 FastAPI 架构实现标准化的流式输出。

```bash
# 前端服务启动
# 前端将会在 ` http://127.0.0.1:50001` 端口部署
python frontend/flask/app.py

# 后端服务启动
# 后端默认端口 8000 端口
python backend/main_fastapi.py
```