#!/usr/bin/env python3
"""
启动IntelliSearch后端服务
"""
import os
import sys
import subprocess
import logging
import dotenv
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
dotenv.load_dotenv()

def check_environment():
    """检查环境变量和依赖"""
    logger.info("🔍 检查环境配置...")

    # 检查必需的环境变量
    required_env_vars = ['DEEPSEEK_API_KEY']
    missing_vars = []

    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.error("请设置环境变量或检查 .env 文件")
        return False

    logger.info("✅ 环境变量检查通过")
    return True

def check_config_files():
    """检查配置文件"""
    logger.info("🔍 检查配置文件...")

    config_file = project_root / "config.json"
    if not config_file.exists():
        logger.error(f"❌ 配置文件不存在: {config_file}")
        return False

    logger.info("✅ 配置文件检查通过")
    return True

def install_requirements():
    """安装Python依赖"""
    logger.info("📦 安装Python依赖...")

    requirements_files = [
        project_root / "requirements.txt",
        project_root / "requirements-fastapi.txt"
    ]

    for req_file in requirements_files:
        if req_file.exists():
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(req_file)
                ], check=True, capture_output=True, text=True)
                logger.info(f"✅ 安装依赖成功: {req_file.name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ 安装依赖失败 {req_file.name}: {e}")
                logger.error(f"错误输出: {e.stderr}")
                return False

    return True

def start_backend():
    """启动后端服务"""
    logger.info("🚀 启动IntelliSearch后端服务...")

    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)

    try:
        # 启动FastAPI服务
        cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main_fastapi:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]

        logger.info(f"执行命令: {' '.join(cmd)}")

        # 启动服务
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        logger.info("✅ 后端服务启动成功!")
        logger.info("🌐 API地址: http://localhost:8000")
        logger.info("📚 API文档: http://localhost:8000/docs")
        logger.info("📝 前端页面: http://localhost:8000")
        logger.info("💡 按 Ctrl+C 停止服务")

        # 实时输出日志
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                print(f"[FastAPI] {line}")

        process.wait()

    except KeyboardInterrupt:
        logger.info("📴 用户中断，正在停止服务...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        logger.info("✅ 服务已停止")

    except Exception as e:
        logger.error(f"❌ 启动服务失败: {e}")
        return False

    return True

def main():
    """主函数"""
    logger.info("🤖 IntelliSearch 后端启动脚本")
    logger.info("=" * 50)

    # 切换到项目根目录
    os.chdir(project_root)

    # 环境检查
    if not check_environment():
        sys.exit(1)

    if not check_config_files():
        sys.exit(1)

    # 安装依赖
    logger.info("🔍 检查Python依赖...")
    try:
        import fastapi
        import uvicorn
        import openai
        import mcp
        logger.info("✅ Python依赖检查通过")
    except ImportError as e:
        logger.warning(f"⚠️ 缺少依赖: {e}")
        if not install_requirements():
            logger.error("❌ 依赖安装失败")
            sys.exit(1)

    # 启动服务
    if not start_backend():
        sys.exit(1)

if __name__ == "__main__":
    main()