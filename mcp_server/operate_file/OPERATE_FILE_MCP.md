# Filesystem MCP Server (v3.0)

本模块提供了一套安全、健壮且原生的文件系统操作工具集，旨在替代不稳定的 Shell 命令注入方式。所有操作均受 `SecurityManager` (V3) 保护，支持细粒度的权限控制和 UI 交互拦截。

## 🛡️ 安全架构

- **拦截机制**: 所有的文件操作在执行前都会经过 `validate_path(path, action)`。
- **Zero Trust**: 默认拒绝所有访问，必须通过 `permissions.json` 或动态 UI 授权。
- **UI 穿透**: 当权限被拒绝时，会自动触发 CLI 端的交互式弹窗，支持临时授权、只读授权等。
- **路径规范**: 自动处理相对路径，支持 `.` (当前目录) 和 `..` (上级目录) 解析，但严禁越狱访问。

## 🛠️ 工具列表 (Tools)

### 1. `ls` (List Directory)

列出指定目录下的文件和文件夹，包含详细元数据。

- **Args**:
  - `path` (str, optional): 目标路径，默认为当前目录 `.`。
- **Output**: 表格化文本，显示 Type (DIR/FILE), Size, Modified Time, Name。
- **Implementation**: `list_ops.py` (Native `pathlib`)

### 2. `tree` (Directory Tree)

以树形结构递归展示目录，支持深度控制。**推荐用于快速了解项目结构。**

- **Args**:
  - `path` (str, optional): 根路径，默认为 `.`。
  - `max_depth` (int, optional): 递归深度。`-1` 为无限，建议设为 `2` 或 `3` 以防 Token 爆炸。
- **Output**: 可视化 ASCII 树。
- **Implementation**: `list_ops.py`

### 3. `cat` (Read File)

智能读取文件内容，具备自动编码检测能力。

- **Args**:
  - `path` (str): 文件路径。
- **Features**:
  - **Auto-Encoding**: 依次尝试 `utf-8` -> `gbk` -> `latin-1`，解决乱码问题。
  - **Binary Protection**: 如果检测到二进制内容（NULL字节），会自动截断并提示，防止乱码刷屏。
  - **Rich Support**: 支持 `.pdf` 文本提取。
  - **Excel**: `.xlsx/.xls` 预览已禁用，请使用自定义 Python 脚本读取。
- **Implementation**: `read_ops.py`

### 4. `search_files` (Grep)

在指定目录下递归搜索包含特定关键词的文本文件。

- **Args**:
  - `path` (str): 搜索根目录。
  - `pattern` (str): 搜索关键词（暂不支持正则，仅字符串匹配）。
- **Features**:
  - 自动跳过常用二进制文件（.exe, .pyc, .png 等）。
  - 自动进行二进制内容检测（Head check）。
  - 支持多种编码读取，确保中文内容可被搜到。
- **Output**: 匹配的文件路径及所在行内容预览。
- **Implementation**: `read_ops.py`

### 5. `touch` (Write/Create)

创建新文件或**覆盖**现有文件。

- **Args**:
  - `path` (str): 目标路径。
  - `content` (str): 写入的全量内容。
- **Warning**: 此操作会覆盖原文件，不可逆。
- **Implementation**: `write_ops.py`

### 6. `append` (Append Text)

向文件末尾追加内容。**推荐日志记录或增量写入。**

- **Args**:
  - `path` (str): 目标路径。
  - `content` (str): 追加的文本内容（自动处理换行符）。
- **Features**: 使用 `open(..., 'a')` 模式，避免 Shell 重定向的编码问题。
- **Implementation**: `write_ops.py`

### 7. `mkdir` (Make Directory)

创建目录（支持递归）。

- **Args**:
  - `path` (str): 目标路径。
- **Features**: 类似于 `mkdir -p`，如果父目录不存在会自动创建。
- **Implementation**: `manage_ops.py`

### 8. `copy` (Copy File/Dir)

复制文件或整个文件夹。

- **Args**:
  - `src` (str): 源路径。
  - `dest` (str): 目标路径。
- **Features**: 自动识别是文件还是文件夹，调用 `shutil.copy2` 或 `shutil.copytree`。
- **Implementation**: `manage_ops.py`

### 9. `mv` (Move/Rename)

移动或重命名文件/文件夹。

- **Args**:
  - `src` (str): 源路径。
  - `dest` (str): 目标路径。
- **Features**: 跨盘符移动时自动处理复制+删除逻辑。
- **Implementation**: `manage_ops.py`

### 10. `rm` (Remove)

删除文件或文件夹。

- **Args**:
  - `path` (str): 目标路径。
- **Warning**: **高危操作**。支持递归删除非空文件夹。
- **Implementation**: `manage_ops.py`

## 💡 开发指南

### 何时使用 Native Tool vs `execute_command`?

✅ **优先使用 Filesystem Native Tools**:

- 所有的文件增删改查操作
- 需要跨平台兼容性 (Windows/Linux/Mac)
- 需要处理中文路径或内容
- 需要安全权限管控

❌ **仅在以下情况使用 `execute_command`**:

- 需要调用系统特有命令 (如 `ipconfig`, `git status`, `python script.py`)
- 需要 Shell 管道操作 (虽然建议用 python 逻辑替代)

### 异常处理

所有工具在遇到权限问题时会抛出 `SecurityError`，遇到 IO 问题会返回清晰的错误字符串（`Error: ...`），不会导致 Agent 崩溃。

## 🔐 UI 穿透 Patch 位置与目的

- [cli.py](cli.py#L33-L43)：引入权限 UI 处理器，导入失败时降级兼容。
- [cli.py](cli.py#L809-L883)：UI 穿透重试循环，捕获权限拒绝，弹窗授权并重试/终止。
- [agents/mcp_agent.py](agents/mcp_agent.py#L153-L166)：推理失败时对权限拒绝透传，避免包装成通用错误。
- [agents/mcp_agent.py](agents/mcp_agent.py#L230-L247)：工具调用被拒绝时回滚最后的 tool-call 消息，避免污染对话。
- [agents/mcp_agent.py](agents/mcp_agent.py#L283-L286)：遇到权限拒绝直接抛出，交由 CLI UI 处理。
- [tools/mcp_base.py](tools/mcp_base.py#L211-L285)：解析工具结果并在发现权限拒绝时抛出异常，触发 UI 交互。

## 🚀 今后可能的改进方向 (Roadmap)

### 1. 🔍 增强搜索能力
- **正则支持**: 升级 `search_files` 以支持 Regex 模式匹配，不仅仅是简单的子串查找。
- **模糊搜索**: 对文件名进行模糊匹配 (Fuzzy Match)。

### 2. 📊 轻量级结构化数据读取
- **Excel/CSV 恢复**: 目前为防止卡顿禁用了 Excel 预览。未来可引入轻量级（非 Pandas）解析器，仅读取前 N 行或特定 Sheet，避免在大文件上挂起。
- **JSON Stream**: 对超大 JSON 文件支持流式读取 (ijson)，避免全量加载内存。

### 3. 🛡️ 细粒度权限控制
- **Regex 路径白名单**: `permissions.json` 支持正则规则，而不仅是具体路径。
- **操作类型隔离**: 区分 `READ` 和 `WRITE` 权限，允许 "只读" 模式的安全浏览。

### 4. ⚡ 性能优化
- **Async IO**: 将文件操作升级为 `aiofiles`，进一步提升并发场景下的吞吐量。
- **缓存机制**: 对高频访问的目录结构 (`ls`, `tree`) 增加短期缓存 (TTL)。

### 5. 📦 压缩包支持
- **Zip/Tar 预览**: 无需解压即可列出压缩包内容 (`ls_archive`) 或读取其中特定文件。
