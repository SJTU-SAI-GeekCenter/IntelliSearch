<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/Intellisearch-v3.1.png" alt="IntelliSearch" />
  </a>
</div>

<h1 align="center">
  IntelliSearch V3.1: Unifying Search, Empowering Action
</h1>

<div align="center">
<a href="https://sjtu-sai-geekcenter.github.io/IntelliSearch/DEV_SETUP" target="_blank">
  <img src="https://img.shields.io/badge/Dev Document-IntelliSearch-green.svg" alt="Webpage"/></a>  
  <a href="./README.md" target="_blank"><img src="https://img.shields.io/badge/English-README-pink.svg" alt="README (English Version)"/></a>
  <a href="./README_ZH.md" target="_blank"><img src="https://img.shields.io/badge/Chinses-README_ZH-red.svg" alt="README (Chinese Version)"/></a>
</div>


IntelliSearch began as a simple search agent based on the MCP (Model Context Protocol) protocol, with the vision of evolving into a lightweight, decoupled, and extensible Agentic Infrastructure and ecosystem foundation. It integrates agent topology, multi-dimensional internal context memory and external document management, dynamic external tool scheduling and environmental interaction mechanisms, as well as multi-agent communication protocols, providing developers with a framework that balances ease of use and flexibility.

## IntelliSearch-v3.1

IntelliSearch-v3.1 (SJTU AI - Intelligent Search) is the second model release in the IntelliSearch agent series. Through the MCP protocol, it achieves integration of multi-dimensio nal, multi-source high-quality information sources and tools, while providing a simple sequential context memory module that significantly expands the boundaries and exploration capabilities of language models. IntelliSearch integrates numerous high-quality MCP tools, including:

**Search Tools:**
- Web Search (`Google Search`, `Zhipu AI Search`, `Web Content Parser`)
- GitHub Search - Repository, code, user, Issue, and PR search
- Academic Search (`Google Scholar`, `arXiv` latest papers)
- Geographic Information Search (Amap API - route planning, geocoding, POI search)
- Bilibili Video Search
- Douban Movie/Book/Review Search
- 12306 Train Information Query
- WeChat Official Account Article Search
- Local Semantic Search (RAG - supports PDF, TXT, MD, DOCX)
- SAI Memos Knowledge Base Search

**Operation Tools:**
- Browser Automation (Playwright - web navigation, interaction, content extraction)
- File System Operations (create, read, write, delete, supports CSV/PDF/JSON)
- Python Code Execution (IPython backend - state persistence, result capture)
- Terminal Command Execution (timeout control, output capture)
- Basic Tool Kit (date/time, UUID, random numbers, and other utilities)

<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="./assets/cli_interface_demo.png" alt="IntelliSearch" />
  </a>
</div>

### Developer Guide

See [DEV_SETUP](./docs/DEV_SETUP.md) for details

## IntelliSearch-v3.1 BackBone

To support the evolution of IntelliSearch-v3.1 into more personalized and flexible agent module designs, we implemented a version-level project refactoring and update (IntelliSearch-v3.1 BackBone). This aims to build a lightweight yet efficient layered agent module design, providing infrastructure support for upper-level applications.

### Design Philosophy

Adopts a **layered architecture** design that clearly separates system responsibilities into the following layers:

- **Core Layer** (`core/`): Defines abstract base classes and data models
  - `BaseAgent`: Abstract base class for all Agents
  - `AgentFactory`: Agent factory pattern implementation
  - `AgentRequest`/`AgentResponse`: Unified request/response models

- **Agent Layer** (`agents/`): Concrete Agent implementations
  - `MCPBaseAgent`: Main Agent with integrated MCP tools

- **Memory Layer** (`memory/`): Conversation context management & external knowledge base component management
  - `BaseMemory`: Memory abstraction interface
  - `SequentialMemory`: Linear context management implementation

- **Tools Layer** (`tools/`): Tool invocation interfaces based on MCP protocol communication & environment simulation interfaces
  - `MCPBase`: MCP tool communication component
  - `MultiServerManager`: MCP server lifecycle management

- **UI Layer** (`ui/`): Unified CLI user interface components
