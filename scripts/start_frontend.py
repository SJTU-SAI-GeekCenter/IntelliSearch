#!/usr/bin/env python3
"""
启动IntelliSearch前端服务（简单HTTP服务器）
"""
import os
import sys
import subprocess
import http.server
import socketserver
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_frontend():
    """启动前端静态文件服务器"""
    # 优先使用docs目录（现有前端代码）
    frontend_dir = project_root / "docs"
    if not frontend_dir.exists():
        frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return False

    print("🎨 启动IntelliSearch前端服务...")
    print(f"📁 前端目录: {frontend_dir}")

    # 切换到前端目录
    os.chdir(frontend_dir)

    print(f"🔍 当前工作目录: {os.getcwd()}")
    print(f"📋 检查关键文件:")

    # 检查关键文件是否存在
    key_files = ['index.html', 'css/styles.css', 'js/app.js']
    for file in key_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - 不存在!")
    print()

    # 配置服务器
    PORT = 3020

    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            """自定义日志格式"""
            print(f"[{self.log_date_time_string()}] {format %args}")

        def do_GET(self):
            """处理GET请求"""
            print(f"📥 请求: {self.path}")

            # 处理根路径
            if self.path == '/':
                self.path = '/index.html'

            # 调用父类方法
            return super().do_GET()

    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ 前端服务启动成功!")
            print(f"🌐 前端地址: http://localhost:{PORT}")
            print(f"💡 按 Ctrl+C 停止服务")
            print("=" * 50)

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n📴 用户中断，正在停止前端服务...")
        print("✅ 前端服务已停止")

    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请检查是否有其他服务运行")
        else:
            print(f"❌ 启动前端服务失败: {e}")
        return False

    return True

if __name__ == "__main__":
    start_frontend()