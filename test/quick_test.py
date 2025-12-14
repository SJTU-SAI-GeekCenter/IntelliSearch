#!/usr/bin/env python3
"""
快速测试脚本 - 检查后端API是否正常运行
"""

import requests
import json
import time

def quick_test():
    """快速测试后端API"""
    base_url = "http://localhost:8000"

    print("🔍 快速测试后端API...")
    print("-" * 40)

    # 1. 测试健康检查
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        return False

    # 2. 测试工具列表
    try:
        response = requests.get(f"{base_url}/api/chat/tools", timeout=10)
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ 工具列表正常 (共 {len(tools.get('tools', []))} 个工具)")
        else:
            print(f"❌ 工具列表获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 工具列表请求异常: {e}")
        return False

    # 3. 测试简单聊天
    try:
        payload = {
            "message": "你好",
            "session_id": "quick_test",
            "use_tools": False
        }

        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get('content', '')
            if content:
                print(f"✅ 聊天接口正常 (响应长度: {len(content)} 字符)")
            else:
                print("❌ 聊天接口返回空内容")
                return False
        else:
            print(f"❌ 聊天接口失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误详情: {error_data}")
            except:
                print(f"   错误文本: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天接口请求异常: {e}")
        return False

    print("-" * 40)
    print("🎉 所有基础测试通过！后端API工作正常。")
    return True

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)