# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IntelliSearch is an intelligent search system based on MCP (Model Context Protocol), featuring a layered architecture that integrates multiple data sources and tools.

**Core Architecture:**

- **Core Layer** (`core/`): Abstract base classes and data models
  - `BaseAgent`: Abstract base class for all Agents, defines unified `inference()` interface
  - `AgentFactory`: Factory pattern implementation, supports dynamic registration and creation
  - `AgentRequest`/`AgentResponse`: Unified request/response data models (Pydantic)

- **Agent Layer** (`agents/`): Concrete Agent implementations
  - `MCPBaseAgent`: Main Agent with MCP tools, supports multi-turn conversation and tool calls

- **Memory Layer** (`memory/`): Conversation context management
  - `BaseMemory`: Memory abstraction interface
  - `SequentialMemory`: Linear context management, maintains conversation history

- **Tools Layer** (`tools/`): MCP protocol communication and environment interaction
  - `MCPBase`: MCP communication component for tool discovery, execution, and response handling
  - `MultiServerManager`: MCP server lifecycle management
  - `ToolCache`: Tool call caching mechanism

- **UI Layer** (`ui/`): Unified CLI user interface components

## Development Setup

### Environment

Uses `uv` for dependency management and isolation. Requires Python 3.12+.

### Configuration

Main config file: `config/config.yaml`

Generate config with:
```bash
bash setup.sh
```

Config includes:
- `agent`: Agent type, model name, system prompt path
- `mcp`: MCP server connection config, port settings
- `cache`: Tool cache configuration
- `env`: API keys and auth credentials

### Backend Services

Some MCP servers require backend services:

```bash
# Start all services (RAG: 39255, IPython: 39256)
python backend/tool_backend/run.py

# Stop all services
python backend/tool_backend/run.py --stop

# Check status
python backend/tool_backend/run.py --status
```

Services start in tmux sessions automatically.

### Embedding Models

Local RAG search requires embedding models at `./models/all-MiniLM-L6-v2/`

## Common Commands

### Running

```bash
# CLI mode (primary)
python cli.py
```

### Testing

```bash
# All tests
pytest

# Specific file
pytest test/test_mcp_tool.py

# Specific function
pytest test/test_rag_service.py::test_rag_search

# Verbose
pytest -v
```

### Dependencies

```bash
# Install/sync
uv sync

# Activate
source .venv/bin/activate
```

## Architecture Notes

### Extending Agents

1. Create new class in `agents/`, inherit `BaseAgent`
2. Implement `inference(self, request: AgentRequest) -> AgentResponse`
3. Register with `AgentFactory.register_agent()`

Example:
```python
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse

class MyCustomAgent(BaseAgent):
    def __init__(self, name: str = "MyAgent"):
        super().__init__(name=name)

    def inference(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            status="success",
            answer="response",
            metadata={}
        )

# Register
from core.factory import AgentFactory
AgentFactory.register_agent("my_agent", MyCustomAgent)
```

### MCP Tool Integration

MCP servers configured in `config/config.yaml`:
- `command`: Start command (`npx` or `uvx`)
- `args`: Command arguments
- `env`: Environment variables (API keys)

Tool call flow:
1. `MCPBaseAgent.inference()` receives request
2. `MCPBase.list_tools()` discovers available tools
3. LLM decides which tools to call
4. `MCPBase.get_tool_response()` executes tools
5. Results returned to LLM for continued reasoning

### Memory Management

Agent uses `SequentialMemory` for conversation history:
- Automatically maintains system prompt
- Stores conversation turns chronologically
- Provides `get_view("chat_messages")` for LLM-compatible format

### Config Loading

Use `Config` class from `config/config_loader.py`:
```python
from config.config_loader import Config

config = Config(config_file_path="config/config.yaml")
config.load_config(override=True)
```

## Project Structure

```
IntelliSearch-v2/
├── agents/          # Agent implementations
├── backend/         # Backend services (FastAPI, tool backends)
├── cli.py           # CLI entry point
├── config/          # Configuration files
├── core/            # Core abstractions and factory
├── data/            # Data directory
├── docs/            # Documentation
├── frontend/        # Web frontend (WIP)
├── log/             # Log files
├── mcp_server/      # MCP server configs and custom servers
│   ├── search_web/  # Web search
│   ├── search_github/ # GitHub search
│   ├── search_scholar/ # Academic search
│   ├── operate_*/   # Various operation tools
│   └── ...
├── memory/          # Memory management
├── prompts/         # System prompts
├── test/            # Tests
├── tools/           # MCP communication
└── ui/              # UI components
```

## Important Notes

1. **Start backend first** - Must run `python backend/tool_backend/run.py` before using RAG/IPython tools
2. **Config priority** - Environment variables override `config.yaml`
3. **Server selection** - Choose which MCP servers to load in `server_choice` field
4. **Logging** - Use `get_logger()` from `core/logger.py` for unified logging
5. **Agent creation** - Always use `AgentFactory.create_agent()`, never instantiate directly
