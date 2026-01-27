# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IntelliSearch is an intelligent search aggregation platform based on the MCP (Model Context Protocol) protocol. It integrates multiple search tools (Google, Bilibili, Douban, Scholar, 12306, WeChat, Amap, etc.) to enhance agent search capabilities through MCP servers.

**Key Architecture Pattern**: The system uses a Factory pattern for agent creation and an abstract base class for agent implementations, making it easy to extend with new agent types and MCP tools.

## Essential Commands

### Environment Setup

```bash
# Install dependencies (requires uv)
uv sync
source .venv/bin/activate

# Initialize submodules if needed
git submodule init
git submodule update
```

### Backend Services

Some MCP servers require backend services to be running:

```bash
# Start required backend services (local_sai on port 39255, ipython_backend on port 39256)
bash scripts/backend.sh

# Check service status
bash scripts/backend.sh status

# Stop services
bash scripts/backend.sh stop
```

### Running the Application

**CLI Mode** (for development):
```bash
python cli.py
```

**Web Mode** (for production/demo):
```bash
# Terminal 1: Start FastAPI backend (port 8001)
python backend/main_fastapi.py

# Terminal 2: Start Flask frontend (port 50001)
python frontend/flask/app.py
```

### Configuration

Before running, ensure proper configuration:

1. **Environment Variables** (`.env` file):
   - `OPENAI_API_KEY`: LLM API key (OpenAI SDK format)
   - `BASE_URL`: LLM base URL
   - `ZHIPU_API_KEY`: For web search
   - `SERPER_API_KEY`: For Google search

2. **MCP Server Configuration** (`config/config.json`):
   - Copy from `config/config.example.json`
   - Add API keys for various MCP servers
   - Configure file paths as needed
   - Supports stdio-based MCP servers

3. **Local RAG Model**:
   - Download `all-MiniLM-L6-v2` model to `./models/` directory
   - Required for SAI local search functionality

## Code Architecture

### Core Components

**agent Architecture**:
- `core/base.py`: Abstract `BaseAgent` class defining the agent interface
- `core/schema.py`: `AgentRequest` and `AgentResponse` data models
- `core/factory.py`: `AgentFactory` for creating agent instances (Factory pattern)
- `agents/mcp_agent.py`: `MCPBaseAgent` - main agent implementation with MCP tool integration

**MCP Integration**:
- `mcp_module/server_manager.py`: Manages multiple MCP server connections
- `mcp_module/connector.py`: Handles MCP protocol communication
- `mcp_module/tool_cache.py`: Caches tool results for performance
- `mcp_server/`: Individual MCP server implementations (web_search, bilibili_search, scholar_search, etc.)

**UI Layer**:
- `ui/theme.py`: Color scheme and styling constants
- `ui/tool_ui.py`: Tool call display utilities
- `ui/status_manager.py`: Status tracking and display
- `ui/loading_messages.py`: Random loading messages for UX

**API Layer**:
- `backend/main_fastapi.py`: FastAPI application entry point
- `backend/api/chat_api.py`: Chat endpoint implementation

### Agent Factory Pattern

When adding a new agent type:

1. Create a new agent class inheriting from `BaseAgent` in `agents/`
2. Implement the `inference(request: AgentRequest) -> AgentResponse` method
3. Register with `AgentFactory.register_agent()` (optional if using static registration)

Example:
```python
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse

class MyCustomAgent(BaseAgent):
    def __init__(self, name: str = "MyAgent"):
        super().__init__(name=name)

    def inference(self, request: AgentRequest) -> AgentResponse:
        # Implementation
        return AgentResponse(
            status="success",
            answer="Response text",
            metadata={}
        )

# Register with factory
AgentFactory.register_agent("custom", MyCustomAgent)
```

### MCP Server Integration

MCP servers are configured in `config/config.json` with:
- `command`: Command to start the server
- `args`: Command arguments
- `env`: Required environment variables
- `description`: Server purpose

To add a new MCP server:
1. Implement server in `mcp_server/your_server/`
2. Add configuration to `config/config.json`
3. Server will be automatically loaded by `MultiServerManager`

### Request/Response Flow

1. User sends query via CLI or Web UI
2. Request wrapped in `AgentRequest` object
3. Agent created via `AgentFactory`
4. Agent's `inference()` method processes request:
   - Loads MCP tools from configured servers
   - Executes LLM with tool definitions
   - Handles tool calls in a loop (max `max_tool_call` iterations)
   - Maintains conversation history
5. Returns `AgentResponse` with status, answer, and metadata

## Development Guidelines

### Code Style
- Follow Python type hints (all public APIs)
- Use English for docstrings and comments
- Maintain structured, modular code (avoid top-level business logic)
- Prefer `class` and `function` abstractions over scripts
- Use the `logging` module instead of `print` (except for CLI final output)

### Testing
- Test files located in individual MCP server directories (e.g., `mcp_server/*/test_*.py`)
- No centralized test suite currently exists
- Use `python mcp_server/[server_name]/test_file.py` to run specific tests

### Key Files to Understand
- `cli.py`: Main CLI entry point with Rich UI
- `core/factory.py`: Agent creation and registration
- `agents/mcp_agent.py`: Core agent logic with MCP integration
- `mcp_module/server_manager.py`: MCP server lifecycle management
- `config/config.example.json`: Template for MCP server configuration

## Common Issues

1. **Port conflicts**: Backend services (39255, 39256) must be running before CLI/web start
2. **Missing API keys**: Ensure `.env` and `config/config.json` are properly configured
3. **Missing model**: Download `all-MiniLM-L6-v2` to `./models/` for local search
4. **MCP server failures**: Check individual server logs in `log/` directory