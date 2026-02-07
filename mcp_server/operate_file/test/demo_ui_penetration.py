import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Path
sys.path.append(os.getcwd())

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession
from ui.permission_ui import handle_permission_error
from mcp_server.operate_file.security import ImplicitDenyError, ExplicitDenyError


async def run_client_loop():
    print("🚀 Starting IntelliSearch Client (with UI Penetration)...")

    # 模拟目标路径
    target_path = Path(
        "d:/geek-centre/IntelliSearch/mcp_server/filesystem/test/secret_data.txt"
    ).resolve()

    # 启动 MCP Server 子进程
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.operate_file.server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. 尝试调用 (预期失败)
            print(f"\n[Client] Requesting 'touch' on {target_path}...")

            try:
                # 第一次尝试
                await session.call_tool(
                    "touch", arguments={"path": str(target_path), "content": "secret"}
                )
                print("[Client] ✅ Success on first try! (Unexpected)")
            except Exception as e:
                error_msg = str(e)
                print(f"[Client] ❌ Operation Failed: {error_msg}")

                # 2. 触发 UI 穿透逻辑
                # 判断是否为权限错误 (MCP协议通常返回 Tool execution error)
                # 这里简单判断字符串内容，或者解析错误码
                is_permission_error = (
                    "Access Denied" in error_msg or "denied" in error_msg.lower()
                )

                if is_permission_error:
                    # 模拟将 RPC 错误转换为 Python 异常对象给 UI
                    # 在实际框架中，Client 会解析错误 Code
                    security_error = ImplicitDenyError(error_msg)

                    print("\n[Client] ⚠️  Triggering Permission UI...")
                    authorized = handle_permission_error(
                        security_error, context_path=str(target_path)
                    )

                    if authorized:
                        print(
                            "\n[Client] 🔄 Authorization received. Retrying operation..."
                        )
                        try:
                            # 3. 重试 (预期成功 - 因为 Server 会 Hot Reload)
                            await session.call_tool(
                                "touch",
                                arguments={
                                    "path": str(target_path),
                                    "content": "secret",
                                },
                            )
                            print(
                                f"[Client] ✅ Retry Successful! File created at {target_path}"
                            )
                        except Exception as retry_e:
                            print(f"[Client] ❌ Retry Failed: {retry_e}")
                    else:
                        print("\n[Client] 🛑 User denied authorization. Aborting.")
                else:
                    print("[Client] Not a permission error, re-raising.")


if __name__ == "__main__":
    try:
        asyncio.run(run_client_loop())
    except KeyboardInterrupt:
        print("\nBye!")
