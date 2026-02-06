<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/Intellisearch-v3.1.png" alt="IntelliSearch" />
  </a>
</div>

IntelliSearch 从一个基于 MCP (Model Context Protocol) 协议的简单搜索智能体出发，志在演化成为一个集成智能体拓扑结构、多维内在上下文记忆和外部文档管理、动态外部工具调度与环境交互机制以及多智能体通信机制的轻量解耦、可扩展的智能体基建和生态底座(Agentic Infra)，为开发者提供兼具易用性和灵活性的开发框架。

## IntelliSearch-v3.1

IntelliSearch-v3.1（交小AI-智搜）为 IntelliSearch 系列智能体发布的第二个模型，通过 MCP 协议实现了多维度多源高质量信息源和工具的整合，并提供简单的顺序上下文记忆模块，极大的拓宽了语言模型的边界和探索能力。智搜集成了多种 MCP 优质工具，包括：

**搜索类工具:**
- 网页搜索 (`Google Search`, `Zhipu AI Search`, `Web Content Parser`)
- GitHub 搜索 - 仓库、代码、用户、Issue 和 PR 搜索
- 学术搜索 (`Google Scholar`, `arXiv` 最新论文)
- 地理信息搜索 (高德地图 API - 路线规划、地理编码、POI 搜索)
- Bilibili 视频搜索
- 豆瓣影音书评搜索
- 12306 火车信息查询
- 微信公众号文章搜索
- 本地语义搜索 (RAG - 支持 PDF、TXT、MD、DOCX)
- SAI Memos 知识库搜索

**操作类工具:**
- 浏览器自动化 (Playwright - 网页导航、交互、内容提取)
- 文件系统操作 (创建、读取、写入、删除，支持 CSV/PDF/JSON)
- Python 代码执行 (IPython 后端 - 状态持久化、结果捕获)
- 终端命令执行 (超时控制、输出捕获)
- 基础工具集 (日期时间、UUID、随机数等实用工具)

<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/cli_interface_demo.png" alt="IntelliSearch" />
  </a>
</div>

### 开发者指南

详见 [DEV_SETUP](./docs/DEV_SETUP.md)

## IntelliSearch-v3.1 BackBone

为了支持 IntelliSearch-v3.1 演化出更个性化、更灵活的若干智能体模块设计，IntelliSearch-v3.1 实现了版本级的项目重构和更新 (IntelliSearch-v3.1 BackBone)，志在搭建轻量化但高效的智能体模块分层设计，为上层建筑提供基建支持。

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
