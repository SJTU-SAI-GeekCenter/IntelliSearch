<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=900&size=50&pause=50&color=000000&center=true&vCenter=true&width=600&height=80&lines=IntelliSearch" alt="Typing SVG" />
  </a>
</div>

# IntelliSearch

> [!IMPORTANT]
> The boundaries of searching capabilities are the boundaries of agents.

IntelliSearch is an intelligent search aggregation platform based on the MCP (Model Context Protocol) protocol, designed to enhance the search boundary capabilities of agents, enabling models to serve more complex search tasks. IntelliSearch integrates multiple high-quality MCP search tools, including:

- Classic and powerful web search tools (`Google Search`, `ZHIPU_search`, `web_parse`)
- Geographic information search (Amap MCP Server)
- Bilibili video search (Bilibili MCP Server)
- Douban movie review search (Douban MCP Server)
- Academic search (Scholar Search Server)
- 12306 train information search (12306 MCP Server)
- WeChat Official Account search (Wechat Search)
- SAI self-built database search (SAI Local Search)
- Python code execution (IPython MCP Server), providing agents with a powerful dynamic code execution environment.

## Demo

> [!NOTE]
> Will be released in future versions.

## Developer Guide

> [!NOTE]
> Below is a minimalist development and reproduction guide for developers. PRs are welcome!

For any questions, please contact [yangxiyuan@sjtu.edu.cn](mailto:yangxiyuan@sjtu.edu.cn)!

### Environment Setup

```bash
# Clone the project
git clone https://github.com/xiyuanyang-code/IntelliSearch.git

# Initialize submodules
git submodule init

# Install dependencies
uv sync
source .venv/bin/activate
```

### Pre-Usage Configuration

#### API Keys Configuration

Create a `.env` file with the following environment variables:

```bash
# OPENAI_API_KEY supports OpenAI SDK mode
OPENAI_API_KEY=your-api-key
BASE_URL=your-base-url

# ZHIPU_API_KEY supports web search
ZHIPU_API_KEY=your-api-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# SERPER_API_KEY for web search and other tools
SERPER_API_KEY=your-api-key
```

To ensure the normal execution of agent conversation and search functions, the following API keys need to be set:

- Model API key and baseurl, supporting OpenAI SDK Format
- `ZHIPU_API_KEY` is mainly used for high-quality Chinese web search
    - Register at [ZHIPU_OFFICIAL_WEBSITES](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) for model services
    - This key can also be used for model services
- `SERPER_API_KEY` is mainly used for Google series high-quality information source search
    - Register at [SERPER_OFFICIAL_WEBSITES](https://serper.dev/dashboard)
    - Each new registered user gets 2500 free credits

#### MCP Server Configuration

To ensure speed and stability, all search tools are **deployed locally** and use stdio for MCP communication. Before starting MCP servers, the following configuration is required:

- Copy `config.json` from `config.example.json`
    - See [Config Example](./config.example.json) for more details
- Add several API keys and settings
    - `ZHIPU_API_KEY` and `SERPER_API_KEY` for `web_search` tools
    - `SESSDATA`, `bili_jct`, and `buvid3` for Bilibili Search tools ([Bilibili MCP](https://github.com/L-Chris/bilibili-mcp))
    - `COOKIE` for `douban_search` ([Douban MCP](https://github.com/moria97/douban-mcp))
    - `AMAP_MAPS_API_KEY` for `amap-mcp-server` ([Amap MCP Server](https://lbs.amap.com/api/mcp-server/create-project-and-key))
- Change the file path

> [!IMPORTANT]
> All stdio MCP servers are supported! You can easily add your custom tools and MCP servers yourself.

#### SAI Local Search Configuration

This repository uses a RAG system to search the SAI self-built high-quality database, separated as a FastAPI backend service. Therefore, before local deployment, you need to deploy the `models/all-MiniLM-L6-v2` folder in the `./models` directory. Download the model from [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) or [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2). Download commands can be found on their official websites.

#### Backend Service Startup

In MCP servers, `ipython-mcp` and `sai-local-search` require backend service communication, so you need to start the backend service before using them:

- `ipython-mcp` is deployed on local port 39255
- `local_sai_search` is deployed on local port 39256

```bash
# Clear corresponding ports and start services
bash scripts/backend.sh

# Check current service status
bash scripts/backend.sh status

# Stop services
bash scripts/backend.sh stop
```

### Usage

> [!IMPORTANT]
> Before proceeding with this section, make sure you have completed the above configuration steps.

IntelliSearch provides two usage methods:

- **CLI Usage**: Use directly in command line, efficient and convenient for developers to develop new features
- **Web Interface**: Use FastAPI framework for backend model service deployment, combined with frontend web rendering, suitable for product demonstration and user usage in production environments.

#### Command Line Usage

```bash
python backend/cli_v2.py
# Supports streaming output
```

#### Web Usage

IntelliSearch also supports local web deployment with FastAPI backend for standardized streaming output.

```bash
# Start frontend service
# Frontend will be deployed on port 50001
python frontend/flask/app.py

# Start backend service
# Backend default port 8000
python backend/main_fastapi.py
```
