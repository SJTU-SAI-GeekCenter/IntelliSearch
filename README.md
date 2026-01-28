# IntelliSearch

<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/IntelliSearch.png" alt="IntelliSearch" />
  </a>
</div>

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

![CLI Interface Demo](./assets/cli_interface_demo.png)

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
MEMOS_API_KEY="your-memos-api-key"
MEMOS_BASE_URL="https://memos.memtensor.cn/api/openmem/v1"
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

To ensure speed and stability, all search tools are **deployed locally** and use stdio for MCP communication. Before starting, complete the following configuration:

1. Copy the MCP server configuration file:
   ```bash
   cp config/config.example.json config/config.json
   ```

2. Add API keys and settings in `config/config.json`:
   - `ZHIPU_API_KEY` and `SERPER_API_KEY` for `web_search` tools
   - `SESSDATA`, `bili_jct`, and `buvid3` for Bilibili Search tools ([How to get](https://github.com/L-Chris/bilibili-mcp))
   - `COOKIE` for `douban_search` ([Douban MCP](https://github.com/moria97/douban-mcp))
   - `AMAP_MAPS_API_KEY` for `amap-mcp-server` ([Apply here](https://lbs.amap.com/api/mcp-server/create-project-and-key))

3. Modify file paths as needed

> [!IMPORTANT]
> All stdio MCP servers are supported! You can easily add your custom tools and MCP servers.

#### SAI Local Search Configuration

This repository uses a RAG system to search the SAI self-built high-quality database, separated as a FastAPI backend service. Therefore, before local deployment, you need to deploy the `models/all-MiniLM-L6-v2` folder in the `./models` directory. Download the model from [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) or [ModelScope](https://www.modelscope.cn/models/AI-ModelScope/all-MiniLM-L6-v2). Download commands can be found on their official websites.

#### Backend Service Startup

Some MCP servers require backend services to be running:

- `local_sai` (SAI local RAG search service) on port 39255
- `ipython_backend` (Python code execution service) on port 39256

```bash
# Start backend services (automatically detects and clears occupied ports)
bash start_backend.sh

# Check service status
bash start_backend.sh status

# Stop services
bash start_backend.sh stop
```

### Usage

> [!IMPORTANT]
> Before proceeding with this section, make sure you have completed the above configuration steps.

IntelliSearch provides two usage methods:

- **CLI Usage**: Use directly in command line, efficient and convenient for developers to test and add new features
- **Web Interface**: Use FastAPI framework for backend model service deployment, combined with frontend web rendering, suitable for product demonstration and user usage in production environments.

#### Command Line Usage

```bash
python cli.py
```

#### Web Usage

> [!IMPORTANT]
> Refactoring, currently not available.

IntelliSearch also supports local web deployment with FastAPI backend for standardized streaming output.

```bash
# Terminal 1: Start FastAPI backend (default port 8001)
python backend/main_fastapi.py

# Terminal 2: Start Flask frontend (default port 50001)
python frontend/flask/app.py
```

## Project Architecture

IntelliSearch adopts a **layered architecture** design with clear separation of concerns:

- **Core Layer** (`core/`): Defines abstract base classes and data models
  - `BaseAgent`: Abstract base class for all agents
  - `AgentFactory`: Agent factory pattern implementation
  - `AgentRequest`/`AgentResponse`: Unified request/response models

- **Agent Layer** (`agents/`): Concrete agent implementations
  - `MCPBaseAgent`: Main agent with MCP tool integration

- **Memory Layer** (`memory/`): Conversation context management
  - `BaseMemory`: Memory abstraction interface
  - `SequentialMemory`: Linear context management implementation

- **Tools Layer** (`tools/`): MCP protocol communication
  - `MCPBase`: MCP tool communication component
  - `MultiServerManager`: MCP server lifecycle management

- **UI Layer** (`ui/`): Unified user interface components
- **API Layer** (`backend/`): Web API interfaces

This architecture design makes the system highly extensible. You can easily:
- Add new agent types (inherit from `BaseAgent`)
- Implement custom memory management strategies (implement `BaseMemory`)
- Integrate new MCP servers (configure in `config/config.json`)

For more detailed architecture documentation, see [CLAUDE.md](./CLAUDE.md).
