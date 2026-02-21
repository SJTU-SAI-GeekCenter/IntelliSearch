<div style="text-align: center;">
  <a href="https://git.io/typing-svg">
    <img src="docs/assets/Intellisearch-v3.1.png" alt="IntelliSearch" />
  </a>
</div>

<h1 align="center">
  IntelliSearch V3.1: Unifying Search, Empowering Action
</h1>

<div align="center">
  <a href="https://sjtu-sai-geekcenter.github.io/IntelliSearch/" target="_blank">
  <img src="https://img.shields.io/badge/Web Pages-IntelliSearch-blue.svg" alt="Webpage"/></a>
  <a href="https://sjtu-sai-geekcenter.github.io/IntelliSearch/DEV_SETUP" target="_blank">
  <img src="https://img.shields.io/badge/Dev Document-IntelliSearch-green.svg" alt="Webpage"/></a>  
  <a href="./README.md" target="_blank"><img src="https://img.shields.io/badge/English-README-pink.svg" alt="README (English Version)"/></a>
  <a href="./README_ZH.md" target="_blank"><img src="https://img.shields.io/badge/Chinses-README_ZH-red.svg" alt="README (Chinese Version)"/></a>
</div>

IntelliSearch (SJTU AI-Intelligent Search) originated as a specialized search agent powered by the Model Context Protocol. Today, it has evolved into a lightweight, decoupled, and highly extensible **Agentic Infrastructure**. By integrating advanced agent topologies, multi-dimensional memory systems, and dynamic tool scheduling, IntelliSearch provides a foundational ecosystem that balances developer-friendly ease of use with industrial-grade flexibility.

> [!IMPORTANT]
> We are delighted to announce the second agent release of IntelliSearch agent series: **IntelliSearch-V3.1** is released and open-sourced!
> See [Project Pages](https://sjtu-sai-geekcenter.github.io/IntelliSearch/) for more fancy demos and features!

## IntelliSearch V3.1

IntelliSearch V3.1 has achieved an all-round comprehensive upgrade, significantly expanding the boundaries of language models. New features including:

- 🛠️ **IntelliSearch-Toolkit**: We introduce IntelliSearch-Toolkit, a high quality toolkit including multi-source multi-domain **SEARCH** tools and safe **OPERATE** tools with environment interactions. It also supports extensible MCP-based tools for customization and advanced workflows.
  - **Search Tools**: Multi-source, multi-domain search engines
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
  - **Operation Tools:**: safety and interactions
    - Browser Automation (Playwright - web navigation, interaction, content extraction)
    - File System Operations (create, read, write, delete, supports CSV/PDF/JSON)
    - Python Code Execution (IPython backend - state persistence, result capture)
    - Terminal Command Execution (timeout control, output capture)
    - Basic Tool Kit (date/time, UUID, random numbers, and other utilities)

- 🌏 **Agent Universe**: Provides a pluggable **agent architecture** supporting multiple agent structures for different tasks. Many more agents are on the way!
- 🧠 **Long Horizon Memories**: Supports **pluggable long-term memory systems** for maintaining conversation context across sessions. Sequential memory architecture enables agents to remember and reason over extended interactions with persistent storage.
- 💻 **Multi-Backend Services**: Offers both **Web** and **CLI** backend modes for flexible deployment. One-click setup with zero configuration for quick start, while supporting deep customization for open-source developers.


## DEV and Usage Guide

- [DEV_SETUP](./docs/DEV_SETUP.md) for setup and usage for developers.
- [DEV_ARCHITECTURE](./docs/DEV_ARCHITECTURE.md) for agentic system design and overall architecture for IntelliSearch.
- For more demos and feature demonstrations, see [Project Pages](https://sjtu-sai-geekcenter.github.io/IntelliSearch/)!
