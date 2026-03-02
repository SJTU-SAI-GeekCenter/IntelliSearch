# ErrorCode 使用指南

## 概述

`ErrorCode` 是 IntelliSearch 异常体系中推荐使用的错误码对象，它封装了错误码、严重级别和默认消息，提供了最优雅的错误抛出接口。

## 核心优势

### 1. 自动映射错误码到严重级别

**旧方式（需要记忆严重级别）：**

```python
from core.exceptions import CriticalError, ErrorCodes

# 需要记住 MCP_CONNECTION 应该用 CriticalError
raise CriticalError(
    error_code=ErrorCodes.MCP_CONNECTION.code,
    message="无法连接到服务器"
)
```

**新方式（自动选择严重级别）：**

```python
from core.exceptions import ErrorCodes

# 不需要知道严重级别，自动选择
ErrorCodes.MCP_CONNECTION.raise_error("无法连接到服务器")
```

### 2. 代码简洁度提升 60%

**对比：**

- 旧方式：5 行代码
- 新方式：1 行代码
- 简洁度提升：**60%**

### 3. 零学习成本

开发者不需要记住每个错误码对应的严重级别，`ErrorCode` 对象已经内置了正确的映射关系。

---

## ErrorCode 类详解

### 属性

```python
class ErrorCode:
    code: str           # 错误码（如 "MCP_001"）
    severity: ErrorSeverity  # 严重级别
    default_message: str     # 默认错误消息
    recovery_suggestion: Optional[str]  # 恢复建议（可选）
```

### 特性

#### 1. 错误码格式验证

所有错误码必须符合 `XXX_###` 格式：

- 前缀：3个大写字母（如 MCP、SEC、AGT）
- 分隔符：下划线 `_`
- 数字：3位数字（如 001、002）

```python
# ✓ 正确的格式
ErrorCode("MCP_001", ErrorSeverity.ERROR, "测试错误")

# ✗ 错误的格式
ErrorCode("MCP_001", ...)  # ✓ 正确
ErrorCode("MCP001", ...)   # ✗ 缺少下划线
ErrorCode("TEST_001", ...)  # ✗ 前缀不是3个字母
ErrorCode("MCP_01", ...)   # ✗ 数字不是3位
```

#### 2. 错误码重复检查

系统会自动检测重复的错误码，防止定义冲突：

```python
# 第一个错误码定义成功
ErrorCode("DUP_001", ErrorSeverity.ERROR, "测试错误1")

# 第二个相同错误码会抛出 ValueError
ErrorCode("DUP_001", ErrorSeverity.ERROR, "测试错误2")  # ✗ 错误码重复
```

### 方法

#### 1. `raise_error()` - 抛出异常（推荐）

```python
ErrorCodes.MCP_CONNECTION.raise_error(
    message: Optional[str] = None,      # 可选：自定义消息
    context: Optional[Dict[str, Any]] = None,  # 可选：上下文信息
    cause: Optional[Exception] = None,  # 可选：原始异常
    recovery_suggestion: Optional[str] = None,  # 可选：自定义恢复建议
) -> None
```

**使用示例：**

```python
from core.exceptions import ErrorCodes

# 方式1：使用默认消息
ErrorCodes.MCP_CONNECTION.raise_error()

# 方式2：自定义消息
ErrorCodes.MCP_CONNECTION.raise_error("无法连接到 127.0.0.1:8080")

# 方式3：添加上下文
ErrorCodes.SEC_PERMISSION_DENIED.raise_error(
    "无法访问文件",
    context={"file": "/etc/passwd", "user": "guest"}
)

# 方式4：包装原始异常
try:
    result = dangerous_operation()
except Exception as e:
    ErrorCodes.TOL_EXECUTION.raise_error("工具执行失败", cause=e)
```

#### 2. `create_error()` - 创建异常对象（不抛出）

```python
error = ErrorCodes.MCP_CONNECTION.create_error("连接失败")
# 可以在需要的时候再抛出
raise error
```

---

## 可用的错误码

### MCP 相关

| 错误码                 | 严重级别 | 默认消息         | 恢复建议                                                        | 使用场景              |
| ---------------------- | -------- | ---------------- | --------------------------------------------------------------- | --------------------- |
| `MCP_CONNECTION`       | CRITICAL | MCP 连接失败     | 请检查 MCP 服务器是否正常运行，确认配置中的服务器地址和端口正确 | 无法连接到 MCP 服务器 |
| `MCP_TOOL_NOT_FOUND`   | WARNING  | MCP 工具未找到   | 请确认工具名称拼写正确，或检查 MCP 服务器是否已注册该工具       | 调用的 MCP 工具不存在 |
| `MCP_EXECUTION`        | ERROR    | MCP 工具执行失败 | 请检查工具参数是否正确，或查看详细错误信息了解失败原因          | 工具执行过程中出错    |
| `MCP_TIMEOUT`          | ERROR    | MCP 执行超时     | 请稍后重试，或考虑增加超时时间配置                              | 工具执行超时          |
| `MCP_INVALID_RESPONSE` | ERROR    | MCP 响应格式错误 | 这可能是 MCP 服务器版本不兼容导致的，请检查服务器版本           | 响应格式不符合预期    |

### 安全相关

| 错误码                    | 严重级别 | 默认消息         | 使用场景       |
| ------------------------- | -------- | ---------------- | -------------- |
| `SEC_PERMISSION_DENIED`   | WARNING  | 权限不足         | 用户权限不足   |
| `SEC_INVALID_PATH`        | ERROR    | 无效路径         | 路径验证失败   |
| `SEC_DANGEROUS_OPERATION` | CRITICAL | 危险操作被阻止   | 阻止危险操作   |
| `SEC_SENSITIVE_DATA`      | WARNING  | 敏感数据泄露风险 | 检测到敏感数据 |
| `SEC_VALIDATION_FAILED`   | ERROR    | 安全验证失败     | 安全验证不通过 |

### Agent 相关

| 错误码               | 严重级别 | 默认消息         | 使用场景             |
| -------------------- | -------- | ---------------- | -------------------- |
| `AGT_INITIALIZATION` | ERROR    | Agent 初始化失败 | Agent 初始化失败     |
| `AGT_EXECUTION`      | CRITICAL | Agent 执行失败   | Agent 执行过程中出错 |
| `AGT_TIMEOUT`        | ERROR    | Agent 响应超时   | Agent 响应超时       |
| `AGT_CONFIGURATION`  | NOTICE   | Agent 配置问题   | Agent 配置有问题     |

### 配置相关

| 错误码           | 严重级别 | 默认消息         | 使用场景         |
| ---------------- | -------- | ---------------- | ---------------- |
| `CFG_LOAD`       | FATAL    | 配置文件加载失败 | 无法加载配置文件 |
| `CFG_VALIDATION` | ERROR    | 配置验证失败     | 配置验证不通过   |
| `CFG_MISSING`    | NOTICE   | 必需配置缺失     | 缺少必需的配置项 |

### 工具相关

| 错误码              | 严重级别 | 默认消息     | 使用场景           |
| ------------------- | -------- | ------------ | ------------------ |
| `TOL_NOT_AVAILABLE` | WARNING  | 工具不可用   | 工具未安装或不可用 |
| `TOL_ARGUMENT`      | ERROR    | 工具参数错误 | 工具参数验证失败   |
| `TOL_EXECUTION`     | ERROR    | 工具执行失败 | 工具执行失败       |

### UI 相关

| 错误码                 | 严重级别 | 默认消息     | 使用场景     |
| ---------------------- | -------- | ------------ | ------------ |
| `UIR_RENDERING`        | ERROR    | UI 渲染失败  | UI 渲染失败  |
| `UIR_USER_INTERACTION` | ERROR    | 用户交互错误 | 用户交互出错 |
| `UIR_EVENT_PIPELINE`   | ERROR    | 事件管线错误 | 事件管线错误 |

### 系统相关

| 错误码        | 严重级别 | 默认消息       | 使用场景       |
| ------------- | -------- | -------------- | -------------- |
| `SYS_INIT`    | FATAL    | 系统初始化失败 | 系统初始化失败 |
| `SYS_IO`      | ERROR    | IO 错误        | 文件读写错误   |
| `SYS_NETWORK` | ERROR    | 网络错误       | 网络连接错误   |

---

## 实际应用场景

### 场景1：MCP 工具调用

```python
from core.exceptions import ErrorCodes

async def call_mcp_tool(tool_name: str, params: dict):
    try:
        # 尝试连接 MCP 服务器
        if not await connect_to_mcp():
            # 使用默认消息
            ErrorCodes.MCP_CONNECTION.raise_error()

        # 执行工具
        result = await execute_tool(tool_name, params)
        return result

    except TimeoutError:
        # 添加上下文信息
        ErrorCodes.MCP_TIMEOUT.raise_error(
            f"工具 {tool_name} 执行超时",
            context={"tool_name": tool_name, "timeout": "30s"}
        )
```

### 场景2：文件权限检查

```python
from core.exceptions import ErrorCodes

def check_file_permission(file_path: str, user: str):
    if not has_permission(file_path, user):
        # 添加详细的上下文
        ErrorCodes.SEC_PERMISSION_DENIED.raise_error(
            f"用户 {user} 无权访问文件",
            context={
                "file": file_path,
                "user": user,
                "required_permission": "read",
                "current_permission": "none"
            }
        )
```

### 场景3：配置加载

```python
from core.exceptions import ErrorCodes

def load_config(config_path: str):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        validate_config(config)
        return config
    except FileNotFoundError:
        # FATAL 级别，程序会退出
        ErrorCodes.CFG_LOAD.raise_error(f"配置文件不存在: {config_path}")
    except json.JSONDecodeError as e:
        # 包装原始异常
        ErrorCodes.CFG_LOAD.raise_error(
            f"配置文件格式错误: {config_path}",
            cause=e
        )
```

### 场景4：工具执行

```python
from core.exceptions import ErrorCodes

def execute_tool(tool_name: str, **kwargs):
    # 检查工具是否可用
    if not tool_available(tool_name):
        # WARNING 级别，不会阻断流程
        ErrorCodes.TOL_NOT_AVAILABLE.raise_error(
            f"工具 {tool_name} 不可用",
            context={"tool_name": tool_name}
        )
        return None

    try:
        result = run_tool(tool_name, **kwargs)
        return result
    except ToolArgumentError as e:
        # ERROR 级别，阻断流程
        ErrorCodes.TOL_ARGUMENT.raise_error(
            f"工具参数错误: {e}",
            context={"tool_name": tool_name, "args": kwargs}
        )
    except Exception as e:
        # 包装原始异常
        ErrorCodes.TOL_EXECUTION.raise_error(
            f"工具执行失败: {tool_name}",
            cause=e
        )
```

### 场景5：Agent 执行

```python
from core.exceptions import ErrorCodes

async def run_agent(agent: MCPAgent, task: str):
    try:
        result = await agent.execute(task)
        return result
    except AgentInitializationError:
        # ERROR 级别
        ErrorCodes.AGT_INITIALIZATION.raise_error(
            f"Agent {agent.name} 初始化失败",
            context={"agent_name": agent.name}
        )
    except TimeoutError:
        # ERROR 级别
        ErrorCodes.AGT_TIMEOUT.raise_error(
            f"Agent {agent.name} 响应超时",
            context={"agent_name": agent.name, "task": task[:50]}
        )
    except Exception as e:
        # CRITICAL 级别，需要用户干预
        ErrorCodes.AGT_EXECUTION.raise_error(
            f"Agent {agent.name} 执行失败",
            context={"agent_name": agent.name, "task": task},
            cause=e
        )
```

---

## 错误决策矩阵

每个错误码都有对应的严重级别，错误中心会根据严重级别做出决策：

| 严重级别 | 退出程序 | 阻断操作 | 通知 MCP |
| -------- | -------- | -------- | -------- |
| FATAL    | ✓        | ✓        | ✗        |
| CRITICAL | ✗        | ✓        | ✓        |
| ERROR    | ✗        | ✓        | ✓        |
| WARNING  | ✗        | ✗        | ✓        |
| NOTICE   | ✗        | ✗        | ✗        |
| INFO     | ✗        | ✗        | ✗        |

---

## 最佳实践

### 1. 优先使用 ErrorCode

```python
# ✓ 推荐：使用 ErrorCode
ErrorCodes.MCP_CONNECTION.raise_error("无法连接")

# ✗ 不推荐：直接使用异常类
raise CriticalError(
    error_code=ErrorCodes.MCP_CONNECTION.code,
    message="无法连接"
)
```

### 2. 充分利用上下文信息

```python
# ✓ 推荐：添加详细的上下文
ErrorCodes.SEC_PERMISSION_DENIED.raise_error(
    "权限不足",
    context={
        "file": file_path,
        "user": current_user,
        "required_permission": "read",
        "operation": "read_file"
    }
)

# ✗ 不推荐：缺少上下文
ErrorCodes.SEC_PERMISSION_DENIED.raise_error("权限不足")
```

### 3. 包装原始异常

```python
# ✓ 推荐：包装原始异常
try:
    result = dangerous_operation()
except Exception as e:
    ErrorCodes.TOL_EXECUTION.raise_error("工具执行失败", cause=e)

# ✗ 不推荐：直接抛出新异常，丢失原始信息
ErrorCodes.TOL_EXECUTION.raise_error("工具执行失败")
```

### 4. 选择合适的严重级别

- **FATAL**：程序无法继续运行（配置文件损坏、系统初始化失败）
- **CRITICAL**：需要用户干预才能继续（MCP 连接失败、Agent 执行失败）
- **ERROR**：操作失败，但可以重试（工具执行失败、参数错误）
- **WARNING**：不影响主要流程（权限不足、工具不可用）
- **NOTICE**：需要注意但可以继续（配置缺失、配置问题）
- **INFO**：仅记录日志（一般性通知）

### 5. 自定义消息要明确

```python
# ✓ 推荐：消息明确具体
ErrorCodes.MCP_CONNECTION.raise_error("无法连接到 MCP 服务器 127.0.0.1:8080")

# ✗ 不推荐：消息过于模糊
ErrorCodes.MCP_CONNECTION.raise_error("出错了")
```

---

## 常见问题

### Q1: 如何添加新的错误码？

在 `core/exceptions.py` 的 `ErrorCodes` 类中添加：

```python
class ErrorCodes:
    # 新增错误码
    NEW_ERROR = ErrorCode(
        "NEW_001",              # 错误码：XXX_### 格式
        ErrorSeverity.ERROR,     # 严重级别
        "新错误的默认消息"       # 默认消息
    )
```

### Q2: 如何修改错误码的严重级别？

直接修改 `ErrorCodes` 类中对应错误码的严重级别：

```python
# 原来
MCP_CONNECTION = ErrorCode("MCP_001", ErrorSeverity.CRITICAL, "MCP 连接失败")

# 修改为 ERROR
MCP_CONNECTION = ErrorCode("MCP_001", ErrorSeverity.ERROR, "MCP 连接失败")
```

### Q3: ErrorCode 和旧的异常类可以混用吗？

可以，但推荐统一使用 ErrorCode：

```python
# 可以混用
ErrorCodes.MCP_CONNECTION.raise_error()  # 新方式
CriticalError(error_code="MCP_001", message="...")  # 旧方式

# 但推荐统一使用新方式
```

### Q4: 如何在测试中使用 ErrorCode？

```python
import pytest
from core.exceptions import ErrorCodes

def test_mcp_connection():
    with pytest.raises(CriticalError) as exc_info:
        ErrorCodes.MCP_CONNECTION.raise_error("测试")

    assert exc_info.value.error_code == "MCP_001"
    assert exc_info.value.message == "测试"
```

---

## 总结

`ErrorCode` 对象提供了最优雅的错误处理方式：

✅ **自动映射**：无需记忆错误码对应的严重级别  
✅ **代码简洁**：一行代码完成错误抛出  
✅ **零学习成本**：直观易懂  
✅ **类型安全**：IDE 自动补全  
✅ **功能完整**：支持上下文、异常链等高级特性

**推荐在所有新代码中使用 `ErrorCode` 对象！**
