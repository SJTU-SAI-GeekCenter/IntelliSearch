# IPython MCP Server

IPython MCP Server 为智能体提供了动态执行Python代码的能力，通过 session 和 cell 管理来实现持久化的代码执行环境。

## 架构组件

### 1. FastAPI 后端服务 (`ipython_backend.py`)
- **端口**: 39256
- **功能**: 提供 REST API 接口管理 session 和 cell
- **日志**: 记录到 `logs/ipython_backend.log`

### 2. MCP 工具封装 (`server_v2.py`)
- **功能**: 将 FastAPI 服务封装为 MCP 工具，供智能体调用
- **工具**: 11个 MCP 工具，支持完整的 session 和 cell 生命周期管理

### 3. 测试套件 (`test_ipython_backend.py`)
- **功能**: 22个综合测试用例，覆盖所有 API 端点
- **用途**: 验证服务功能正确性

## 核心功能

### Session 管理
- ✅ 创建 session (自动递增的 UUID)
- ✅ 查询所有 session
- ✅ 查询特定 session
- ✅ 删除 session

### Cell 管理
- ✅ 在 session 中添加 cell (自动递增的 ID)
- ✅ 查询 session 中所有 cell
- ✅ 查询特定 cell
- ✅ 删除 cell

### 代码执行
- ✅ 在 session 中执行 Python 代码
- ✅ 变量状态持久化 (跨执行共享)
- ✅ 输出捕获 (stdout/stderr)
- ✅ 错误处理和报告

## MCP 工具列表

### 核心 Session 管理
| 工具名称 | 功能描述 |
|---------|---------|
| `create_ipython_session` | 创建新的 IPython session |
| `list_ipython_sessions` | 列出所有活跃的 session |
| `get_session_info` | 获取特定 session 的详细信息 |
| `delete_ipython_session` | 删除 session 及其所有资源 |

### Cell 管理
| 工具名称 | 功能描述 |
|---------|---------|
| `add_code_cell` | 向 session 添加新的代码 cell |
| `list_session_cells` | 列出 session 中的所有 cell |
| `get_cell_info` | 获取特定 cell 的详细信息 |
| `delete_cell` | 从 session 中删除特定 cell |

### 🚀 智能执行功能
| 工具名称 | 功能描述 |
|---------|---------|
| `execute_session_all_cells` | **按顺序执行session中的所有cell**，变量在cell间持久化 |
| `execute_session_cell` | **执行特定cell**，保持session变量状态 |
| `get_session_execution_status` | 获取session的详细执行状态和变量列表 |
| `smart_session_workflow` | 智能工作流执行（sequential/unexecuted/failed/all） |

### 传统执行和工具
| 工具名称 | 功能描述 |
|---------|---------|
| `execute_python_code` | 在 session 中执行 Python 代码 |
| `check_ipython_health` | 检查后端服务健康状态 |
| `run_quick_python_code` | 快速执行代码（临时 session） |

## 使用示例

### 基础工作流
```python
# 1. 创建 session
session_id = create_ipython_session()

# 2. 添加 cell
cell_id = add_code_cell(session_id, "x = 42\nprint(f'x = {x}')")

# 3. 执行代码
result = execute_python_code(session_id, "y = x * 2\nprint(f'y = {y}')")

# 4. 查看结果
print(result)

# 5. 清理
delete_ipython_session(session_id)
```

### 🚀 智能执行示例

#### 执行整个Session的所有Cells
```python
# 1. 创建session并添加多个cell
session_id = create_ipython_session()
add_code_cell(session_id, "x = 10")
add_code_cell(session_id, "y = x * 2")
add_code_cell(session_id, "print(f'Result: {y}')")

# 2. 一次性执行所有cell（按顺序，变量持久化）
result = execute_session_all_cells(session_id)
print(result)
# 输出:
# --- Cell 1 ---
# --- Cell 2 ---
# --- Cell 3 ---
# Result: 20
```

#### 执行特定Cell
```python
# 重新执行cell 3（可以访问前面cell的变量）
result = execute_session_cell(session_id, 3)
print(result)  # Result: 20

# 修改前面的cell并重新执行
add_code_cell(session_id, "x = 15")  # cell 4
execute_session_cell(session_id, 4)   # 执行新的cell 4
execute_session_cell(session_id, 3)   # 重新执行cell 3，使用新的x值
# 输出: Result: 30
```

#### 查看执行状态
```python
status = get_session_execution_status(session_id)
print(status)
# 输出:
# Session session_1 Execution Status:
#   Total cells: 4
#   Executed cells: 4
#   Available variables: x, y
# Cell Details:
#   ✅ Cell 1: Executed
#   ✅ Cell 2: Executed
#   ✅ Cell 3: Executed
#   ✅ Cell 4: Executed
```

#### 智能工作流
```python
# 执行所有未执行的cell
result = smart_session_workflow(session_id, "unexecuted")

# 重新执行所有cell
result = smart_session_workflow(session_id, "all")
```

### 变量持久化示例
```python
session_id = create_ipython_session()

# 通过execute_python_code设置变量
execute_python_code(session_id, "data = [1, 2, 3, 4, 5]")

# 通过智能执行使用变量
add_code_cell(session_id, "mean_val = statistics.mean(data)")
execute_session_cell(session_id, 1)  # cell 1会自动访问data变量

# 所有执行方式共享同一变量空间
status = get_session_execution_status(session_id)
# 可用变量: data, mean_val
```

## 启动服务

### 1. 启动所有服务
```bash
./run.sh
```

### 2. 单独启动 IPython 后端
```bash
cd mcp_server/python_executor
python ipython_backend.py
```

### 3. 启动 MCP 服务器
```bash
cd mcp_server/python_executor
python server_v2.py
```

## 运行测试

```bash
cd mcp_server/python_executor
python test_ipython_backend.py
```

### 🧪 测试覆盖范围
现在包含 **29个综合测试用例**，覆盖所有功能：

#### 核心功能测试 (15个)
- ✅ 健康检查
- ✅ Session CRUD 操作（创建、查询、删除）
- ✅ Cell CRUD 操作（添加、查询、删除）
- ✅ 代码执行（成功/失败场景）
- ✅ 变量持久化验证

#### 🚀 智能执行功能测试 (7个)
- ✅ 执行整个session的所有cells
- ✅ 执行特定cell
- ✅ 执行状态查询
- ✅ 空session执行处理
- ✅ Cell执行状态持久化
- ✅ 跨cell执行的变量共享

#### 高级场景测试 (7个)
- ✅ 多session并发执行
- ✅ 复杂计算工作流
- ✅ 大量代码执行
- ✅ 错误处理和边界情况
- ✅ 资源清理和内存管理
- ✅ Session隔离性验证

### 测试特点
- 🔄 **自动化资源清理**: 测试完成后自动删除所有创建的资源
- 📊 **详细状态报告**: 每个测试的详细结果和错误信息
- 🛡️ **边界情况测试**: 空session、不存在的资源等场景
- 🔗 **依赖关系测试**: 验证cell之间的变量共享和执行顺序

## 日志管理

日志文件位置: `log/ipython_backend.log`

包含的信息：
- API 请求和响应
- Session 创建/删除
- Cell 添加/删除
- 代码执行结果
- 错误和异常

## 技术特性

### 状态管理
- 每个 session 维护独立的变量空间
- 变量在 session 生命周期内持久存在
- 支持 Python 标准库和第三方模块导入

### 安全性
- 代码在隔离环境中执行
- 自动捕获 stdout/stderr 输出
- 完整的错误堆栈跟踪

### 性能
- 轻量级 session 管理
- 高效的变量状态存储
- 快速的代码执行响应

### 可扩展性
- 模块化架构设计
- 清晰的 API 接口
- 易于添加新功能