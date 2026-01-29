# IntelliSearch

<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/IntelliSearch.png" alt="IntelliSearch" />
  </a>
</div>

IntelliSearch 从一个基于 MCP (Model Context Protocol) 协议的简单搜索智能体出发，志在演化成为一个集成智能体拓扑结构、多维内在上下文记忆和外部文档管理、动态外部工具调度与环境交互机制以及多智能体通信机制的轻量解耦、可扩展的智能体基建和生态底座(Agentic Infra)，为开发者提供兼具易用性和灵活性的开发框架。

## IntelliSearch-v3.0

IntelliSearch-v3.0（交小AI-智搜） 为 IntelliSearch 系列智能体发布的首个模型，通过 MCP 协议实现了多维度多源高质量信息源和工具的整合，并提供简单的顺序上下文记忆模块，极大的拓宽了语言模型的边界和探索能力。智搜集成了多种 MCP 优质搜索工具，包括：

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

<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/cli_interface_demo.png" alt="IntelliSearch" />
  </a>
</div>

### 开发者指南

详见 [DEV_SETUP](./docs/DEV_SETUP.md)

## IntelliSearch-v3.1 BackBone

为了支持 IntelliSearch-v3.1 演化出更个性化、更灵活的若干智能体模块涉及，IntelliSearch-v3.0 实现了版本级的项目重构和更新 (IntelliSearch-v3.1 BackBone)，志在搭建轻量化但高效的智能体模块分层设计，为上层建筑提供基建支持。

### 设计理念

采用了**分层架构**设计，将系统职责清晰分离为以下几层：

- **核心层** (`core/`): 定义抽象基类和数据模型
  - `BaseAgent`: 所有 Agent 的抽象基类
  - `AgentFactory`: Agent 工厂模式实现
  - `AgentRequest`/`AgentResponse`: 统一的请求/响应模型

- **智能体层** (`agents/`): 具体的 Agent 实现
  - `MCPBaseAgent`: 集成 MCP 工具的主 Agent

- **记忆层** (`memory/`): 对话上下文管理 & 外部知识库组件管理
  - `BaseMemory`: 记忆抽象接口
  - `SequentialMemory`: 线性上下文管理实现

- **工具层** (`tools/`): MCP 协议通信为基础的工具调用接口 & 环境模拟接口
  - `MCPBase`: MCP 工具通信组件
  - `MultiServerManager`: MCP 服务器生命周期管理

- **UI 层** (`ui/`): 统一的 CLI 用户界面组件
