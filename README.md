# IntelliSearch

> [!IMPORTANT]
> The boundaries of searching capabilities are the boundaries of agents.

IntelliSearch 是一个基于 MCP (Model Context Protocol) 协议的智能搜索聚合平台，集成了多种垂直搜索引擎和RAG检索功能，现在支持 **IPython 代码执行** 功能，为智能体提供强大的动态代码执行环境。

## Installation

### API-KEY Config

```env
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_URL=https://api.deepseek.com
ZHIPU_API_KEY=your-api-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
SERPER_API_KEY=your-api-key

# RAG settings
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_BASE_URL=https://api.openai-proxy.org/v1
```

### IPython MCP Server Dependencies

The IPython MCP server requires additional dependencies:

```bash
pip install ipython fastapi uvicorn requests
```

### MCP Server Settings

Copy `config.json` from `config.example.json`:

- Add several api-keys and settings
- Change the file path

> [!IMPORTANT]
> All stdio mcp servers are supported! You can easily add your custom tools and mcp servers yourself.

## Usage

### IntelliSearch Service Manager

The project includes a robust service management script `run.sh` for managing all MCP servers:

```bash
# Start all services
./run.sh start

# Start specific services
./run.sh start ipython_backend
./run.sh start local_sai

# Stop services
./run.sh stop
./run.sh stop local_sai

# Restart services
./run.sh restart
./run.sh restart ipython_mcp

# Check service status
./run.sh status

# View logs
./run.sh logs ipython_backend
./run.sh logs ipython_backend --follow

# Get help
./run.sh help
```

#### Available Services:
- **local_sai**: Local SAI Search Service (port: 23225)
- **ipython_backend**: IPython Backend Server (port: 8889)
- **ipython_mcp**: IPython MCP Server

### FastAPI-Design

```bash
bash scripts/start_all.sh
```

### CLI Usage

```bash
python backend/cli.py
```

### Testing

The project includes comprehensive test suites for the IPython MCP server:

```bash
# Quick test for basic functionality
python quick_test.py

# Comprehensive test suite (covers all features)
python test_ipython.py
```

The test suites verify:
- ✅ Server startup and connectivity
- ✅ Session management (CRUD operations)
- ✅ Cell management (CRUD operations)
- ✅ Code execution and state persistence
- ✅ Error handling and edge cases
- ✅ Resource cleanup and memory management


## Features

### 🔍 Search Capabilities
- Web Search Integration
- Academic Search (Scholar)
- Social Media Search (Bilibili, WeChat)
- Local RAG Search with Vector Database
- Database Queries (Douban, Amap Maps)

### 🐍 IPython Code Execution
- **Session-based Python execution** with persistent state
- **Cell-based code management** for organized development
- **Multiple isolated environments** for concurrent tasks
- **Error handling and output capture** for robust execution

### ⚡ Service Management
- **Robust process management** with automatic recovery
- **Service health monitoring** and status reporting
- **Centralized logging** with real-time log tailing
- **Graceful shutdown** and resource cleanup

## Todo List

- Front-End Optimizations
- MCP Servers Optimizations
- IPython Code Execution ✅ (Completed)
- Advanced Analytics Dashboard
- Multi-language Support
