# Dev Architecture for IntelliSearch V3.2

> Still Constructing...

## Overview

## File Structure

```text
.
├── agents
│   ├── __init__.py
│   ├── mcp_agent_async.py
│   └── mcp_agent.py
├── api.py
├── backends
│   ├── __init__.py
│   ├── cli_backend.py
│   ├── tool_backend
│   │   ├── ipython_service.py
│   │   ├── rag_service.py
│   │   ├── rag_src
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   ├── documents.py
│   │   │   ├── embeddings.py
│   │   │   └── README.md
│   │   ├── run.py
│   │   └── sai_update
│   │       ├── generate_slicing.py
│   │       ├── README.md
│   │       └── update.py
│   └── web_backend.py
├── cli.py
├── config
│   ├── __init__.py
│   ├── config_loader.py
│   └── config.example.yaml
├── core
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── logger.py
│   └── schema.py
├── docs
│   ├── assets
│   │   ├── cli_interface_demo.png
│   │   ├── demo
│   │   │   ├── cli_demo1.MOV
│   │   │   ├── cli_demo2.MOV
│   │   │   ├── cli_demo3.MOV
│   │   │   └── cli_demo4.MOV
│   │   ├── IntelliSearch-SAI.png
│   │   ├── Intellisearch-v3.1.png
│   │   └── IntelliSearch.png
│   ├── css
│   │   └── style.css
│   ├── DEV_ARCHITECTURE.md
│   ├── DEV_SETUP.md
│   ├── index.html
│   └── js
│       └── main.js
├── frontend
│   ├── app.py
│   ├── README.md
│   ├── static
│   │   ├── assets
│   │   │   └── sai-square.jpg
│   │   ├── css
│   │   │   ├── admin.css
│   │   │   ├── chat-loading.css
│   │   │   ├── desktop.css
│   │   │   ├── loading-animation.css
│   │   │   ├── main.css
│   │   │   └── mobile.css
│   │   └── js
│   │       ├── auth-loading.js
│   │       ├── chat-loading.js
│   │       ├── desktop_chat.js
│   │       ├── mobile_chat.js
│   │       └── particles.js
│   └── templates
│       ├── admin
│       │   ├── chats.html
│       │   ├── dashboard.html
│       │   ├── login.html
│       │   ├── tokens.html
│       │   └── users.html
│       ├── base.html
│       ├── desktop_chat.html
│       ├── error.html
│       ├── login.html
│       ├── mobile_chat.html
│       ├── register.html
│       └── test_loading.html
├── mcp_server
│   ├── __init__.py
│   ├── base_toolkit
│   │   └── server.py
│   ├── operate_browser
│   │   └── server.py
│   ├── operate_file
│   │   ├── __init__.py
│   │   ├── list_ops.py
│   │   ├── manage_ops.py
│   │   ├── OPERATE_FILE_MCP.md
│   │   ├── permissions.example.json
│   │   ├── read_ops.py
│   │   ├── security.py
│   │   ├── server.py
│   │   ├── test
│   │   │   ├── demo_ui_penetration.py
│   │   │   ├── list_op_test.py
│   │   │   └── preview_permission_ui.py
│   │   └── write_ops.py
│   ├── operate_python
│   │   └── server.py
│   ├── operate_terminal
│   │   └── server.py
│   ├── search_bilibili
│   │   ├── bcut_asr.py
│   │   └── server.py
│   ├── search_geo
│   │   └── server.py
│   ├── search_github
│   │   └── server.py
│   ├── search_local
│   │   └── server.py
│   ├── search_movie
│   │   └── server.py
│   ├── search_sai
│   │   └── server.py
│   ├── search_scholar
│   │   └── server.py
│   ├── search_train
│   │   ├── api_client.py
│   │   ├── server.py
│   │   └── utils.py
│   ├── search_web
│   │   └── server.py
│   └── search_wechat
│       └── server.py
├── memory
│   ├── __init__.py
│   ├── base.py
│   └── sequential.py
├── prompts
│   └── sys_zh.md
├── pyproject.toml
├── README_ZH.md
├── README.md
├── services
│   ├── __init__.py
│   ├── base_service.py
│   ├── cli_service.py
│   └── web_service.py
├── setup.sh
├── test
│   ├── conftest.py
│   ├── pytest.ini
│   ├── README.md
│   ├── run_standard_test.sh
│   └── test_standard_toolkit
│       ├── conftest.py
│       ├── test_mcp_standard.py
│       └── test_params
│           ├── base_toolkit.json
│           ├── operate_browser.json
│           ├── operate_python.json
│           ├── operate_terminal.json
│           ├── search_bilibili.json
│           ├── search_geo.json
│           ├── search_github.json
│           ├── search_local.json
│           ├── search_movie.json
│           ├── search_sai.json
│           ├── search_scholar.json
│           ├── search_train.json
│           └── search_web.json
├── tools
│   ├── __init__.py
│   ├── connector.py
│   ├── mcp_base.py
│   ├── server_manager.py
│   ├── tool_cache.py
│   └── tool_hash.py
└── ui
    ├── __init__.py
    ├── loading_messages.py
    ├── permission_ui.py
    ├── status_manager.py
    ├── theme.py
    ├── tool_call_ui.py
    └── tool_ui.py
```

## Core

### Base

### Factory

### Logger

### Schema

## Config

IntelliSearch 实现了全局配置的一体化和统一化：

- 所有的配置全部存储在 `config/config.yaml` (由 `setup.sh` 生成)
- 系统各个模块利用 `config/config_loader.py` 进行配置读取，不同模块之间的配置相互独立、互不干扰。

Config 采用**单例模式**，正确使用方式如下:

```python
from config.config_loader import Config
```

获取结构化 Config 的方式:

```python
# 方式 A：获取已存在的单例
config = Config.get_instance()
value = config.get("key", default_value)

# 方式 B：创建新实例（仅在进程初始化时）
Config.reset_instance()  # 先重置
config = Config(config_file_path="...")
config.load_config(override=True)
```

## Backends

### Tool Backends

### CLI Backends

### Web Backends

### Code Backend (OpenAI-Compatible API)

Code Backend 提供兼容 OpenAI SDK 的标准化 API 接口，由以下核心组件构成：

- **core/openai_schema.py**: Pydantic 数据模型定义 OpenAI 标准 API 契约（ChatCompletionRequest/Response, ModelsResponse）
- **backend/code_backend.py**: FastAPI 应用层，实现路由注册、Bearer Token 认证、CORS 中间件配置
- **services/code_service.py**: 无状态服务层，负责上下文组装、基于 tiktoken 的精确 token 估算、使用 nest_asyncio 调度底层同步 agent 推理以避免事件循环阻塞

## Agents

### MCP Base Agent

### MCP Async Agent

## FrontEnd (For Webs)

## Services

### CLI Services

### Web Services

## UI

## Test

### Test Standards Toolkit

## Tools

### MCP Servers