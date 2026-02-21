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

IntelliSearch (SJTU AI-Intelligent Search) 最初是一个由 Model Context Protocol 驱动的专用搜索 Agent。如今，它已演进为一个轻量级、解耦且高度可扩展的 **Agent 基础设施**。通过整合先进的 Agent 拓扑结构、多维度记忆系统和动态工具调度，IntelliSearch 提供了一个既易于使用又具备工业级灵活性的基础生态系统。

> [!IMPORTANT]
> 我们很高兴地宣布 IntelliSearch Agent 系列的第二个 Agent 版本：**IntelliSearch-V3.1** 正式发布并开源！
> 更多精彩演示和功能请访问 [项目主页](https://sjtu-sai-geekcenter.github.io/IntelliSearch/)！

## IntelliSearch V3.1

IntelliSearch V3.1 实现了全方位的全面升级，显著扩展了语言模型的能力边界。新特性包括：

- 🛠️ **IntelliSearch-Toolkit**: 我们推出了 IntelliSearch-Toolkit，这是一个高质量的工具包，包含多源多领域的 **搜索 (SEARCH)** 工具和具备环境交互能力的 **操作 (OPERATE)** 工具。同时支持可扩展的基于 MCP 的工具，以实现定制化和高级工作流。
  - **搜索工具**: 多源、多领域搜索引擎
    - 网络搜索 (`Google Search`、`Zhipu AI Search`、`Web Content Parser`)
    - GitHub 搜索 - 仓库、代码、用户、Issue 和 PR 搜索
    - 学术搜索 (`Google Scholar`、`arXiv` 最新论文)
    - 地理信息搜索 (高德地图 API - 路线规划、地理编码、POI 搜索)
    - Bilibili 视频搜索
    - 豆瓣电影/图书/评论搜索
    - 12306 列车信息查询
    - 微信公众号文章搜索
    - 本地语义搜索 (RAG - 支持 PDF、TXT、MD、DOCX)
    - SAI Memos 知识库搜索
  - **操作工具**: 安全与交互
    - 浏览器自动化 (Playwright - 网页导航、交互、内容提取)
    - 文件系统操作 (创建、读取、写入、删除，支持 CSV/PDF/JSON)
    - Python 代码执行 (IPython 后端 - 状态持久化、结果捕获)
    - 终端命令执行 (超时控制、输出捕获)
    - 基础工具包 (日期/时间、UUID、随机数等实用工具)

- 🌏 **Agent 宇宙**: 提供可插拔的 **Agent 架构**，支持针对不同任务的多种 Agent 结构。更多 Agent 正在路上！
- 🧠 **长期记忆**: 支持 **可插拔的长期记忆系统**，用于在跨会话时维护对话上下文。顺序记忆架构使 Agent 能够通过持久化存储记住并推理长期交互。
- 💻 **多后端服务**: 提供 **Web** 和 **CLI** 两种后端模式，支持灵活部署。一键零配置快速启动，同时支持开源开发者深度定制。


## 开发与使用指南

- [DEV_SETUP](./docs/DEV_SETUP.md) - 开发者设置和使用指南
- [DEV_ARCHITECTURE](./docs/DEV_ARCHITECTURE.md) - IntelliSearch 的 Agent 系统设计和整体架构
- 更多演示和功能展示，请访问 [项目主页](https://sjtu-sai-geekcenter.github.io/IntelliSearch/)！
