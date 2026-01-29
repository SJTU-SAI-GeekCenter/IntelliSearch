# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IntelliSearch is an intelligent search aggregation platform based on the MCP (Model Context Protocol) protocol. It integrates multiple search tools (Google, Bilibili, Douban, Scholar, 12306, WeChat, Amap, etc.) to enhance agent search capabilities through MCP servers.

**Key Architecture Pattern**: The system uses a Factory pattern for agent creation and an abstract base class for agent implementations. Recent refactoring has separated concerns into three distinct layers:
- **Agent Layer** (`agents/`): Core agent logic and inference
- **Memory Layer** (`memory/`): Context and conversation management
- **Tools Layer** (`tools/`): MCP protocol communication and server management

## Essential Commands

### Environment Setup

```bash
# Install dependencies (requires uv)
uv sync
source .venv/bin/activate
```

### Backend Services

Some MCP servers require backend services to be running:

```bash
# Start required backend services (local_sai on port 39255, ipython_backend on port 39256)
bash start_backend.sh

# Check service status
bash start_backend.sh status

# Stop services
bash start_backend.sh stop
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

### Layered Architecture

The codebase follows a **layered architecture** with clear separation of concerns:

#### 1. Core Layer (`core/`)
- **Base Abstractions**: Foundation for the entire system
  - `core/base.py`: Abstract `BaseAgent` class defining the agent interface
  - `core/schema.py`: `AgentRequest` and `AgentResponse` unified data models
  - `core/factory.py`: `AgentFactory` for creating agent instances (Factory pattern)

#### 2. Agent Layer (`agents/`)
- **Agent Implementations**: Concrete agent implementations
  - `agents/mcp_agent.py`: `MCPBaseAgent` - main agent with MCP tool integration
  - Uses composition pattern with dedicated Memory and MCP components
  - Orchestrates LLM inference with tool calling loop

#### 3. Memory Layer (`memory/`)
- **Context Management**: Pluggable memory implementations for conversation state
  - `memory/base.py`: Abstract `BaseMemory` defining memory interface
  - `memory/sequential.py`: `SequentialMemory` - linear context management
  - Provides views for LLM (e.g., `get_view("chat_messages")`)
  - Supports serialization/deserialization

#### 4. Tools Layer (`tools/`)
- **MCP Protocol**: All MCP-related communication isolated here
  - `tools/mcp_base.py`: `MCPBase` component for tool operations
  - `tools/server_manager.py`: `MultiServerManager` for MCP server lifecycle
  - `tools/connector.py`: Low-level MCP protocol communication
  - `tools/tool_cache.py`: Caching layer for tool results

#### 5. MCP Server Implementations (`mcp_server/`)
- Individual MCP servers for each search capability:
  - `web_search/`: Google and ZHIPU web search
  - `bilibili_search/`: Bilibili video search
  - `scholar_search/`: Academic paper search
  - `local_sai_search/`: Local RAG-based database search (requires backend service on port 39255)
  - `python_executor/`: Python code execution (requires backend service on port 39256)
  - `douban_search/`, `amap_mcp_server/`, `wechat_search/`, etc.

#### 6. UI Layer (`ui/`)
- `ui/theme.py`: Color scheme and styling constants
- `ui/tool_ui.py`: Tool call display utilities
- `ui/status_manager.py`: Unified status tracking and display
- `ui/loading_messages.py`: Random loading messages for UX

#### 7. API Layer (`backend/`)
- `backend/main_fastapi.py`: FastAPI application entry point (port 8001)
- `backend/api/chat_api.py`: Chat endpoint with streaming support
- `backend/tool_hash.py`: Tool parameter hashing utilities

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

### Component Composition Pattern

The `MCPBaseAgent` uses composition to combine three specialized components:

```python
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from tools.mcp_base import MCPBase
from memory.sequential import SequentialMemory

class MCPBaseAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(name=name)

        # Component 1: Memory for conversation management
        self.memory = SequentialMemory(system_prompt=system_prompt)

        # Component 2: MCPBase for tool communication
        self.mcp_base = MCPBase(config_path=server_config_path)

    def inference(self, request: AgentRequest) -> AgentResponse:
        # Use memory to get chat history
        messages = self.memory.get_view("chat_messages")

        # Use mcp_base to list available tools
        tools = await self.mcp_base.list_tools()

        # Execute tool calling loop
        for iteration in range(self.max_tool_call):
            # LLM inference with tools
            response = self.client.chat.completions.create(
                messages=messages,
                tools=tools
            )

            # Execute tool calls via mcp_base
            if tool_calls:
                results = await self.mcp_base.get_tool_response(tool_calls)

                # Update memory with tool results
                self.memory.add(tool_message)
```

This separation allows you to:
- Swap memory implementations (e.g., from `SequentialMemory` to a vector-based memory)
- Test MCP communication independently
- Reuse `MCPBase` in other agent types

### Request/Response Flow

1. User sends query via CLI (`cli.py`) or Web UI (`backend/main_fastapi.py`)
2. Request wrapped in `AgentRequest` object with prompt and metadata
3. Agent created via `AgentFactory.create_agent(agent_type="mcp_base_agent", ...)`
4. Agent's `inference()` method processes request:
   - Retrieves conversation history from `memory.get_view("chat_messages")`
   - Loads MCP tools via `mcp_base.list_tools()`
   - Executes LLM with tool definitions (OpenAI SDK format)
   - **Tool Calling Loop** (max `max_tool_call` iterations, typically 20):
     - If LLM requests tool calls → execute via `mcp_base.get_tool_response()`
     - Add tool results to memory
     - Make next LLM call with updated context
   - Maintains conversation history via `memory.add()`
5. Returns `AgentResponse` with:
   - `status`: "success", "failed", or "timeout"
   - `answer`: Final text response
   - `metadata`: Intermediate results, tool calls, sources, etc.

## Development Guidelines

### Adding New Functionality

#### Adding a New Agent Type

1. Create a new agent class inheriting from `BaseAgent` in `agents/`
2. Implement the `inference(request: AgentRequest) -> AgentResponse` method
3. Use composition with Memory and MCP components as needed
4. Register with `AgentFactory.register_agent()` (optional if using static registration)

Example:
```python
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse
from memory.sequential import SequentialMemory

class MyCustomAgent(BaseAgent):
    def __init__(self, name: str = "MyAgent"):
        super().__init__(name=name)
        self.memory = SequentialMemory(system_prompt="You are a helper")

    def inference(self, request: AgentRequest) -> AgentResponse:
        # Access conversation history
        messages = self.memory.get_view("chat_messages")
        messages.append({"role": "user", "content": request.prompt})

        # Your logic here
        response = "Processed response"

        # Update memory
        self.memory.add({"role": "assistant", "content": response})

        return AgentResponse(
            status="success",
            answer=response,
            metadata={"iterations": 1}
        )

# Register with factory
AgentFactory.register_agent("custom", MyCustomAgent)
```

#### Adding a New Memory Implementation

1. Inherit from `BaseMemory` in `memory/`
2. Implement all abstract methods: `reset()`, `add()`, `add_many()`, `get_view()`, `export()`, `load()`
3. Support at minimum the `"chat_messages"` view type

Example:
```python
from memory.base import BaseMemory
from typing import List, Dict, Any

class VectorMemory(BaseMemory):
    def __init__(self):
        self.vectors = []

    def reset(self) -> None:
        self.vectors = []

    def add(self, entry: Any) -> None:
        # Add entry to vector store
        pass

    def get_view(self, view_type: str, **kwargs) -> Any:
        if view_type == "chat_messages":
            # Retrieve relevant messages
            return self._retrieve_relevant()
        raise NotImplementedError
```

#### Adding a New MCP Server

1. Implement server in `mcp_server/your_server/`
2. Create `server.py` that exposes tools via MCP protocol
3. Add configuration to `config/config.json`:
   ```json
   {
     "mcpServers": {
       "my_server": {
         "command": "python",
         "args": ["./mcp_server/my_server/server.py"],
         "env": {"API_KEY": "your-key"},
         "description": "My custom MCP server"
       }
     }
   }
   ```
4. Server will be automatically loaded by `MultiServerManager`

### Code Style
- Follow Python type hints (all public APIs)
- Use English for docstrings and comments
- Maintain structured, modular code (avoid top-level business logic)
- Prefer `class` and `function` abstractions over scripts
- Use the `logging` module instead of `print` (except for CLI final output)
- All code must follow the format specified in global CLAUDE.md instructions

### Configuration System

The project uses a hierarchical configuration system:

1. **YAML Configuration** (`config/config.yaml`): Main settings
   - Agent type, model, max_tool_call
   - MCP server config path
   - Cache settings
   - Timeout configurations

2. **Environment Variables** (`.env`): Override YAML settings
   - Format: `AGENT_SECTION_KEY=value` (e.g., `AGENT_MODEL_NAME=gpt-4`)
   - API keys and sensitive data

3. **MCP Server Config** (`config/config.json`): MCP-specific settings
   - Server commands and arguments
   - Per-server environment variables
   - Transport type (stdio/SSE)

### Testing
- Test files located in individual MCP server directories (e.g., `mcp_server/*/test_*.py`)
- No centralized test suite currently exists
- Use `python mcp_server/[server_name]/test_file.py` to run specific tests

### Key Files for Understanding the Codebase

**Start here** (in order):
1. `core/schema.py`: Understand unified `AgentRequest` and `AgentResponse` models
2. `core/base.py`: Understand the `BaseAgent` interface
3. `memory/sequential.py`: See how conversation state is managed
4. `tools/mcp_base.py`: Understand MCP tool communication
5. `agents/mcp_agent.py`: See how components compose in the main agent
6. `cli.py`: CLI entry point showing how everything connects

**Configuration**:
- `config/config.yaml`: Main configuration with agent settings
- `config/config.example.json`: Template for MCP server configuration
- `config/config_loader.py`: Configuration loading logic

**Backend Services**:
- `start_backend.sh`: Service startup script
- `mcp_server/local_sai_search/rag_service.py`: RAG backend (port 39255)
- `mcp_server/python_executor/ipython_backend.py`: Python execution backend (port 39256)

## Common Issues

1. **Port conflicts**: Backend services (39255, 39256) must be running before CLI/web start
   - Check status: `bash start_backend.sh status`
   - Check logs in `log/` directory

2. **Missing API keys**: Ensure `.env` and `config/config.json` are properly configured
   - Required: `OPENAI_API_KEY`, `BASE_URL`
   - For web search: `ZHIPU_API_KEY`, `SERPER_API_KEY`

3. **Missing model**: Download `all-MiniLM-L6-v2` to `./models/` for local search
   - Required for `local_sai_search` MCP server

4. **MCP server failures**: Check individual server logs in `log/` directory
   - Common issue: stdio transport not working - check command/args in config
   - Use environment variables in MCP config for API keys

5. **Import errors**: Ensure virtual environment is activated
   ```bash
   source .venv/bin/activate
   ```

6. **Memory issues**: Long conversations may hit token limits
   - Adjust `max_tool_call` in config if needed
   - Memory supports truncation via `get_view("chat_messages", max_entries=N)`