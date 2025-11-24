# IntelliSearch - 智能搜索助手

🤖 **IntelliSearch** 是一个基于 MCP (Model Context Protocol) 的智能搜索助手，集成了多种工具调用能力，提供强大的信息检索和对话功能。

## ✨ 特性

- 🧠 **智能对话**: 基于 DeepSeek AI 的强大对话能力
- 🔧 **工具调用**: 支持多种 MCP 工具的自动调用
- 🎨 **现代UI**: 美观的前端界面，带有酷炫的工具调用特效
- 🚀 **高性能**: 基于 FastAPI 的后端架构
- 📝 **会话管理**: 支持多轮对话和会话持久化
- 🔍 **实时响应**: 流式输出，实时显示工具调用过程

## 🏗️ 架构设计

### 后端架构
```
backend/
├── main_fastapi.py          # FastAPI 主应用
├── api/
│   └── chat_api.py          # 聊天 API 路由
├── core/
│   ├── llm_client.py        # LLM 客户端
│   └── mcp_client.py        # MCP 客户端
├── models/
│   └── chat_models.py       # 数据模型
├── cli.py                   # CLI 版本
└── tool_hash.py             # 工具参数修复
```

### 前端架构
```
frontend/
├── index.html               # 主页面
├── styles.css              # 样式文件
└── app.js                  # 应用逻辑
```

### 启动脚本
```
scripts/
├── start_all.sh            # 启动所有服务
├── stop_services.sh        # 停止所有服务
├── start_backend.py        # 启动后端
└── start_frontend.py       # 启动前端
```

## 🚀 快速开始

### 1. 环境准备

确保你已安装 Python 3.8+。

```bash
# 克隆项目
git clone <repository-url>
cd IntelliSearch

# 安装 Python 依赖
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart python-dotenv
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

获取 DeepSeek API Key:
1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册账号并创建 API Key
3. 将 API Key 填入 `.env` 文件

### 3. 配置 MCP 服务

确保 `config.json` 文件存在于项目根目录，并配置你需要的 MCP 服务器。

### 4. 启动服务

#### 一键启动（推荐）

```bash
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

#### 分别启动

```bash
# 启动后端
python scripts/start_backend.py

# 启动前端（新终端）
python scripts/start_frontend.py
```

### 5. 访问应用

- 🌐 前端界面: http://localhost:3000
- 🚀 后端API: http://localhost:8000/api
- 📚 API文档: http://localhost:8000/docs

### 6. 停止服务

```bash
./scripts/stop_services.sh
```

## 🛠️ 使用方法

### 基本对话

1. 在浏览器中打开 http://localhost:3000
2. 在输入框中输入你的问题
3. 点击发送或按 Enter 键
4. AI 助手会回复并可能调用相关工具

### 工具调用

当 AI 需要调用工具时，你会看到：

- 🎯 **工具调用指示器**: 显示当前调用的工具名称
- ✨ **粒子特效**: 工具调用时的视觉特效
- 🏆 **成功标记**: 工具调用完成的动画
- 📋 **工具标签**: 消息中显示调用的工具列表

### 设置选项

点击右上角的设置按钮可以：

- 🔧 启用/禁用工具调用
- 🆔 创建新会话
- 🔗 修改 API 地址

## 📡 API 接口

### 流式聊天接口

```http
POST /api/chat/stream
Content-Type: application/json

{
  "message": "用户消息",
  "session_id": "会话ID（可选）",
  "use_tools": true
}
```

### 非流式聊天接口

```http
POST /api/chat
Content-Type: application/json

{
  "message": "用户消息",
  "session_id": "会话ID（可选）",
  "use_tools": true
}
```

### 获取可用工具

```http
GET /api/tools
```

## 🎨 特效说明

### 工具调用特效
- **调用开始**: 粒子动画 + 旋转工具图标
- **调用中**: 发光边框 + 脉冲动画
- **调用完成**: 成功标记动画

### 消息动画
- **消息出现**: 弹性滑入动画
- **头像悬停**: 缩放效果
- **工具标签**: 渐入动画

## 🐛 故障排除

### 常见问题

1. **环境变量未设置**
   ```bash
   # 检查 .env 文件是否存在且包含正确的 DEEPSEEK_API_KEY
   cat .env
   ```

2. **端口被占用**
   ```bash
   # 停止服务
   ./scripts/stop_services.sh
   ```

3. **依赖安装失败**
   ```bash
   # 更新 pip
   pip install --upgrade pip

   # 重新安装依赖
   pip install -r requirements.txt fastapi uvicorn python-multipart
   ```

### 停止服务

```bash
./scripts/stop_services.sh
```

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的 AI 模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [MCP](https://modelcontextprotocol.io/) - 模型上下文协议

---

⭐ 如果这个项目对你有帮助，请给我们一个 Star！

