# IPython MCP Server

## 任务

我们希望智能体可以通过 `ipython` 来动态的执行 Python 代码，因此可以作为工具封装。

简单来说，你需要在 `mcp_server/python_executor/ipython_backend.py` 中创建一个 FastAPI 后端，支持下面的一些功能：

- 创建一个 session 会话（一个 session 中的变量是追加式的，只有在销毁这个 session 的时候才会被销毁）
- 在 session 中添加 Python 代码 Cell
- 在 session 中删除 Python 代码 Cell
- 查询特定 session 中的 Python 代码的 Cell
- 查询所有 session
- 在 session 中运行特定的 Python 代码
- 删除一个 session

其中每一个 session 都有一个 uuid 从 1 开始逐渐递增，在每一个 session 中有若干个 cell cell-id 也是从 1 开始逐渐递增，注意删除的 session-id 和 cell-id 不可以复用，相当于你需要维护一个持久化的计数器。

在完成 FastAPI 的后端服务后，你可以使用 request 库来封装，模仿 v1 版本的 MCP Python 风格给我提供 `mcp_server/python_executor/server_v2.py`

请你在写 MCP 工具的时候，从智能体调用工具的视角写非常清楚的 Docstring（英文）

在完成之后，可以在 `mcp_server/python_executor` 文件夹中创建一个 test 的脚本文件，测试一些基本功能，设置不少于 20 个测试样例

## 完成 `run.sh`

我希望你在 `run.sh` 中可以控制启动若干后端服务，注意！MCP Server 的启动服务和这个脚本无关，现在，你需要更新 `run.sh` 并启动：

- local sai search 的端口（端口 23225）
- ipython backend 的后端端口（端口 8889）

你可以根据 README 中设计的功能来实现你的脚本