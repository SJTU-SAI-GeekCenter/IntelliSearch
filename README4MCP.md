# MCP Chat for JiaoXiao-AI

## Introduction

在智能体时代，对每一个智能体从零还是手动构建工具的效率及其低下，而 MCP 提供了一套标准的组件和接口模式，实现了第三方工具的接口统一化和高效复用。这可以让大模型快速方便的调用大量工具，与现实世界产生更多链接。

[Official Docs for MCP](https://modelcontextprotocol.io/docs/getting-started/intro).

The core code is in [`mcp_chat.py`](./app/services/mcp_chat.py).

## Tools (for developers)

MCP-Chat 采用和 Base-Chat 相同的接口和模型，关键在于会在后台自动启动 MCP Server 并且将工具调用的操作指南传递给 LLM，具体而言，在新建一轮对话的过程中，MCP-Chat 需要传入定义好的 `availables_tools`.

```python
def stream_chat_response(self, available_tools):
        """
        执行流式响应逻辑（同步版本，兼容 DeepSeek / OpenAI SDK）
        """
        result_text = ""
        if available_tools:
            with self.client.chat.completions.stream(
                model=self.model_name,
                messages=self.history,
                tools=available_tools,
            ) as stream:
                for event in stream:
                    if hasattr(event, "chunk") and event.chunk.choices:
                        delta = event.chunk.choices[0].delta

                        if getattr(delta, "content", None):
                            print(Fore.CYAN + delta.content, end="", flush=True)
                            result_text += delta.content

                        if getattr(delta, "tool_calls", None):
                            for tool in delta.tool_calls:
                                func = getattr(tool, "function", None)
                                if func:
                                    if func.name:
                                        print(
                                            Fore.GREEN + f"\n🔧 Tool name: {func.name}"
                                        )
                                    if func.arguments:
                                        print(
                                            Fore.GREEN + func.arguments,
                                            end="",
                                            flush=True,
                                        )

                final_message = stream.get_final_completion()
                return result_text, final_message
        else:
            # no tools for streaming response
            with self.client.chat.completions.stream(
                model=self.model_name,
                messages=self.history,
            ) as stream:
                for event in stream:
                    if hasattr(event, "chunk") and event.chunk.choices:
                        delta = event.chunk.choices[0].delta

                        if getattr(delta, "content", None):
                            print(Fore.CYAN + delta.content, end="", flush=True)
                            result_text += delta.content

                        if getattr(delta, "tool_calls", None):
                            for tool in delta.tool_calls:
                                func = getattr(tool, "function", None)
                                if func:
                                    if func.name:
                                        print(
                                            Fore.GREEN + f"\n🔧 Tool name: {func.name}"
                                        )
                                    if func.arguments:
                                        print(
                                            Fore.GREEN + func.arguments,
                                            end="",
                                            flush=True,
                                        )

                final_message = stream.get_final_completion()
                return result_text, final_message
```

传入工具的过程是自动的，只需要在 config 文件夹下写好对应的 server 路径和部署方式即可。

### Server List

工具可以分为两类，第一类是**搜索为主的**不会和外部世界产生交互的工具调用，包括：
- 信息搜集和检索
- The key lies in **What it will get**!

第二类是**Agent产生实际操作行为，与外部世界形成交互**的工具调用，例如：
- 本地文件管理和写入
- 打电话等控制个人账户和 APP 行为
- The key lies in **What it will do**!

目前因为网页版的 Web-Chat 受限较多，因此暂时只考虑部署第一类不产生实际效果的搜索类工具，而这一部分部署的关键在于部署搜索**Multi-Source** 的信息检索工具，目前已经接入工具：

- Google Search
- ZHIPU Search（对中文内容搜索更好）
- web parse （对给定 url 进行文字提取，也支持 PDF Parse）
- GitHub Code Search
- Bilibili Video Search
- Weixin Search
- 12306 Tickets Search
- Scholar Search for google
- Douban Search
- Wekipedia Search
- Map Search (Amaps Search)
- Python Code Interpreter
    - Support `ipynb` and other advanced python code interactions.

To be added in the future:

- **Local Search for SAI**

> 对于后续可以实现对一些本地操作（类别二），可开源该框架之后由用户自动接入，实现无代码部署。

### Server Deployment

> [!IMPORTANT]
> 目前暂时只支持 stdio 的方式调用 MCP

在 `mcp_server` 的文件夹下新建目录作为 server 目录，最关键的是启动命令和函数装饰器的设置。例如我们本地定义的简单的一个运行 Python 代码的 server：

```python
@mcp.tool()
async def run_python_code(code: str) -> str:
    """
    运行一段 Python 代码并返回输出结果。
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stderr:
            return f"❌ Error:\n{stderr.decode()}"
        return stdout.decode() or "(no output)"
    except Exception as e:
        return f"Exception: {e}"
```

最关键的是 `config.json` 的定义，具体的定义方式可以参考官方文档，此处给出示例：

```json
{
    "mcpServers": {
        "web_search": {
            "command": "python",
            "args": [
                "/data/xiyuanyang/SJTU-AI-Chat/mcp_server/web_search/server.py"
            ],
            "env": {
                "ZHIPU_API_KEY": "",
                "SERPER_API_KEY": ""
            },
            "description": "Web Search tools to get information on the web"
        },
        "python-exec": {
            "command": "python",
            "args": [
                "/data/xiyuanyang/SJTU-AI-Chat/mcp_server/python_executor/server.py"
            ]
        },
        "bilibili-search": {
            "command": "npx",
            "args": [
                "bilibili-mcp"
            ],
            "description": "B站视频搜索 MCP 服务，可以在AI应用中搜索B站视频内容。"
        },
        "12306-mcp": {
            "command": "npx",
            "args": [
                "-y",
                "12306-mcp"
            ]
        },
        "weixin_search_mcp": {
            "command": "uvx",
            "args": ["weixin_search_mcp", "--transport", "stdio"]
        }
    }
}
```

