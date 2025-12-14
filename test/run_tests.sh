#!/bin/bash

# IntelliSearch 测试运行脚本

echo "🧪 IntelliSearch 后端测试脚本"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查Python依赖..."
python3 -c "import requests; import aiohttp" 2>/dev/null || {
    echo "❌ 缺少必要的Python包，正在安装..."
    pip3 install requests aiohttp
}

# 检查后端服务是否运行
echo "🔍 检查后端服务..."
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ 后端服务未运行，请先启动后端服务："
    echo "   python3 scripts/start_backend.py"
    echo "   或"
    echo "   uvicorn backend.main_fastapi:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ 后端服务正在运行"

# 运行测试
echo ""
echo "🚀 开始运行测试..."
echo ""

# 运行快速测试
echo "1️⃣ 运行快速测试..."
python3 quick_test.py
quick_result=$?

echo ""

if [ $quick_result -eq 0 ]; then
    echo "2️⃣ 运行详细测试..."
    python3 test_backend_api.py
    detailed_result=$?
else
    echo "⚠️  快速测试失败，跳过详细测试"
    detailed_result=1
fi

echo ""
echo "📊 测试总结:"
echo "============"

if [ $quick_result -eq 0 ] && [ $detailed_result -eq 0 ]; then
    echo "🎉 所有测试通过！"
    echo "✅ 后端API工作正常"
else
    echo "❌ 部分测试失败"
    if [ $quick_result -ne 0 ]; then
        echo "   - 快速测试失败"
    fi
    if [ $detailed_result -ne 0 ]; then
        echo "   - 详细测试失败"
    fi
    echo ""
    echo "🔧 故障排除建议:"
    echo "   1. 检查后端服务是否正常启动"
    echo "   2. 检查config.json配置是否正确"
    echo "   3. 检查MCP服务器是否正常启动"
    echo "   4. 查看后端日志了解详细错误信息"
fi

exit $((quick_result + detailed_result))