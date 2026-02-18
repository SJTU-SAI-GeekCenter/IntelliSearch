import asyncio
import sys
import os
from mcp.client.stdio import StdioServerParameters
from mcp.client.session import ClientSession

# 调整路径以便找到模块
sys.path.append(os.getcwd())


async def run():
    # 配置启动参数：就好像 CLI 启动它一样
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.operate_file.server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print(f"Connected. Found tools: {[t.name for t in tools.tools]}")

            # 调用 ls 工具
            print("\nCalling 'ls'...")
            try:
                result = await session.call_tool("ls", arguments={"path": "."})
                print("Result:")
                print(result.content[0].text)
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    from mcp.client.stdio import stdio_client

    asyncio.run(run())
