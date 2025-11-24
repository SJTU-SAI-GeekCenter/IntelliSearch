from mcp.server.fastmcp import FastMCP
import asyncio

mcp = FastMCP("python-exec-server")

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

if __name__ == "__main__":
    mcp.run()
