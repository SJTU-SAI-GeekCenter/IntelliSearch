# IntelliSearch Testing Suite

统一、模块化的 MCP 服务器测试套件,支持通过 JSON 参数文件进行测试配置。

## 默认工具组件测试

IntelliSearch 提供了一套 Python 接口实现的 MCP 高质量工具集，包含多元搜索类，操作类等等工具内容，实现多源多领域信息的搜集和多环境交互的操作。为了保证工具的可用性，在 `test/test_standard_toolkit` 中提供了一套默认工具组件测试单元，支持利用 `pytest` 实现工具集的可用性、IO 耗时等因素的测试。

> 在 `pyproject.toml` 中 uv 依赖中安装了 `pytest`, `pytest-asyncio`, `pytest-xdist`, `pytest-html` 四个 pytest 依赖及相关插件库，可自行安装其他插件库。

### 脚本快速启动

我们在 [`test/run_standard_test.sh`](../test/run_standard_test.sh) 实现了一个脚本的封装，允许一键启动**pytest**进行多个 MCP Server 的并发工具测试。

```bash
bash test/run_standard_test.sh base_toolkit operate_terminal
```

> [!IMPORTANT]
> 若执行并发测试，对于独立的测试用例来说会提升运行效率，但是对于**依赖顺序执行**的测试用例而言，可能会因为执行顺序的差异导致问题。例如 IPython-MCP 的测试组件，建议使用 `pytest -k operate_python` 来执行测试操作。

### `pytest` 命令指南

```bash
# 运行所有测试
pytest

# 运行特定服务器测试
pytest -k base_toolkit          # 基础工具
pytest -k SERVER_NAME 
# 可用的 SERVER_NAME 均对应 mcp_server 中的不同 MCP Server 和工具

# 运行多个服务器
pytest -k "base_toolkit or search_local"

# 查看所有可用测试
pytest --collect-only
```

支持并行执行测试组件：

```bash
# 使用 4 个进程并行运行
pytest -n 4

# 自动检测 CPU 核心数
pytest -n auto
```

失败时立即停止：

```bash
pytest -x            # 第一个失败后停止
pytest -xx           # 两个失败后停止
```

显示最慢的测试:

```bash
pytest --durations=10
```

生成测试报告:

```bash
# 生成 HTML 报告
pytest --html=report.html
```

### 测试文件添加配置

该测试组件支持自定义添加 MCP Server 并且添加个性化的测试用例。

#### 为现有服务器添加测试

所有测试通过 JSON 参数文件配置,位于 `test_standard_toolkit/test_params/` 目录。为现有的 MCP Server 添加测试用例只需要编辑对应的 JSON 文件,例如 `test_standard_toolkit/test_params/base_toolkit.json`:

```json
{
  "tests": [
    {
      "tool": "get_current_date",
      "input_params": {}
    },
    {
      "tool": "calculate_maths",
      "input_params": {
        "expression": "1 + 1"
      }
    }
  ]
}
```

#### Adding MCP Servers

1. 在 `config/config.yaml` 中 `all_servers` 的字段配置 MCP Server
2. 在 `test_standard_toolkit/test_params/` 创建 JSON 文件(文件名为服务器名)
3. 添加测试用例（相同的格式）

示例 - `my_server.json`:

```json
{
  "tests": [
    {
      "tool": "my_tool",
      "input_params": {
        "query": "test"
      }
    }
  ]
}
```

### 测试结果

所有测试结果自动保存到 `test/test_results/` 目录。

## 可插拔的自定义测试实现

> [!IMPORTANT]
> Still on the way...

## 相关文档

- [pytest 文档](https://docs.pytest.org/)
- [项目 CLAUDE.md](../CLAUDE.md)
