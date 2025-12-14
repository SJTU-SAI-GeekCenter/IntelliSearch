#!/usr/bin/env python3
"""
IntelliSearch 后端API测试脚本
用于测试FastAPI后端的各种功能
"""

import asyncio
import json
import requests
import aiohttp
from typing import Dict, Any, Optional

class BackendAPITest:
    """后端API测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> bool:
        """测试健康检查接口"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                print(f"健康检查状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"健康检查响应: {data}")
                    return True
                return False
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False

    async def test_get_tools(self) -> bool:
        """测试获取工具列表接口"""
        try:
            async with self.session.get(f"{self.base_url}/api/chat/tools") as response:
                print(f"获取工具列表状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"可用工具数量: {len(data.get('tools', []))}")
                    tools_list = data.get('tools', [])
                    for tool in tools_list[:3]:  # 只显示前3个工具
                        print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', '')[:80]}...")
                    return True
                else:
                    error_data = await response.text()
                    print(f"获取工具列表失败: {error_data}")
                    return False
        except Exception as e:
            print(f"获取工具列表异常: {e}")
            return False

    async def test_chat_stream(self, message: str = "你好，请介绍一下自己") -> bool:
        """测试聊天流式接口"""
        try:
            payload = {
                "message": message,
                "session_id": "test_session_001",
                "use_tools": True
            }

            print(f"发送测试消息: {message}")
            async with self.session.post(
                f"{self.base_url}/api/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"聊天流式接口状态码: {response.status}")

                if response.status != 200:
                    error_data = await response.text()
                    print(f"聊天接口错误: {error_data}")
                    return False

                content_received = False
                error_received = False

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        try:
                            data = json.loads(line[6:])
                            event_type = data.get('type', '')

                            if event_type == 'content':
                                content = data.get('content', '')
                                print(f"收到内容: {content[:100]}...")
                                content_received = True
                            elif event_type == 'tool_call':
                                tool_name = data.get('tool_name', '')
                                print(f"工具调用: {tool_name}")
                            elif event_type == 'tool_result':
                                print(f"工具结果收到")
                            elif event_type == 'error':
                                error_msg = data.get('error', '')
                                print(f"收到错误: {error_msg}")
                                error_received = True

                        except json.JSONDecodeError:
                            continue

                return content_received and not error_received

        except Exception as e:
            print(f"聊天流式测试异常: {e}")
            return False

    async def test_chat_non_stream(self, message: str = "简单回答：1+1等于几？") -> bool:
        """测试非流式聊天接口"""
        try:
            payload = {
                "message": message,
                "session_id": "test_session_002",
                "use_tools": False
            }

            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"非流式聊天接口状态码: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    content = data.get('content', '')
                    print(f"非流式响应: {content[:100]}...")
                    return len(content) > 0
                else:
                    error_data = await response.text()
                    print(f"非流式聊天错误: {error_data}")
                    return False

        except Exception as e:
            print(f"非流式聊天测试异常: {e}")
            return False

    def test_sync_endpoints(self) -> Dict[str, bool]:
        """测试同步接口"""
        results = {}

        # 测试健康检查
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            results['health_check'] = response.status_code == 200
            print(f"同步健康检查: {'✓' if results['health_check'] else '✗'}")
        except Exception as e:
            results['health_check'] = False
            print(f"同步健康检查失败: {e}")

        # 测试API文档
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            results['api_docs'] = response.status_code == 200
            print(f"API文档访问: {'✓' if results['api_docs'] else '✗'}")
        except Exception as e:
            results['api_docs'] = False
            print(f"API文档访问失败: {e}")

        return results


async def run_comprehensive_test():
    """运行综合测试"""
    print("=" * 60)
    print("IntelliSearch 后端API测试")
    print("=" * 60)

    # 测试同步接口
    print("\n1. 测试同步接口...")
    async with BackendAPITest() as tester:
        sync_results = tester.test_sync_endpoints()

        print("\n2. 测试异步接口...")

        # 测试健康检查
        print("\n2.1 测试健康检查...")
        health_ok = await tester.test_health_check()
        print(f"异步健康检查: {'✓' if health_ok else '✗'}")

        # 测试工具列表
        print("\n2.2 测试工具列表...")
        tools_ok = await tester.test_get_tools()
        print(f"工具列表获取: {'✓' if tools_ok else '✗'}")

        # 测试流式聊天
        print("\n2.3 测试流式聊天...")
        stream_ok = await tester.test_chat_stream()
        print(f"流式聊天: {'✓' if stream_ok else '✗'}")

        # 测试非流式聊天
        print("\n2.4 测试非流式聊天...")
        non_stream_ok = await tester.test_chat_non_stream()
        print(f"非流式聊天: {'✓' if non_stream_ok else '✗'}")

    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)

    all_results = {
        **sync_results,
        'health_check_async': health_ok,
        'tools_list': tools_ok,
        'stream_chat': stream_ok,
        'non_stream_chat': non_stream_ok
    }

    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)

    for test_name, result in all_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20}: {status}")

    print(f"\n总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！后端API工作正常。")
    else:
        print("⚠️  部分测试失败，请检查后端服务。")


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("用法: python test_backend_api.py [选项]")
        print("选项:")
        print("  --help    显示帮助信息")
        print("  --url     指定后端服务URL (默认: http://localhost:8000)")
        return

    # 可指定不同的后端URL
    backend_url = "http://localhost:8000"
    if len(sys.argv) > 1 and sys.argv[1] == "--url" and len(sys.argv) > 2:
        backend_url = sys.argv[2]

    print(f"测试目标: {backend_url}")

    # 运行测试
    try:
        asyncio.run(run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行异常: {e}")


if __name__ == "__main__":
    main()