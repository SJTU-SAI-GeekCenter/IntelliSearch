#!/bin/bash

# IntelliSearch 全服务启动脚本
# 启动后端和前端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}


# 检查配置文件
check_config() {
    log_info "检查配置文件..."

    if [ ! -f "$PROJECT_ROOT/config.json" ]; then
        log_error "config.json 文件不存在"
        log_info "请确保 config.json 文件存在于项目根目录"
        exit 1
    fi

    log_success "配置文件检查通过"
}

# 安装依赖
install_dependencies() {
    log_info "检查Python依赖..."

    # 检查requirements文件
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        log_info "安装依赖包..."
        pip3 install -r "$PROJECT_ROOT/requirements.txt" || {
            log_error "依赖安装失败"
            exit 1
        }
    fi

    log_success "依赖检查通过"
}

# 创建日志目录
create_log_dirs() {
    log_info "创建日志目录..."
    mkdir -p "$PROJECT_ROOT/log"
    mkdir -p "$PROJECT_ROOT/results"
    log_success "目录创建完成"
}

# 启动服务
start_services() {
    log_info "启动IntelliSearch服务..."
    echo "=================================================="

    # 切换到项目根目录
    cd "$PROJECT_ROOT"

    # 启动后端服务
    log_info "启动后端服务..."
    python3 scripts/start_backend.py &
    BACKEND_PID=$!

    # 等待后端启动
    sleep 3

    # 检查后端是否启动成功
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "后端服务启动失败"
        exit 1
    fi

    log_success "后端服务已启动 (PID: $BACKEND_PID)"

    # 启动前端服务
    log_info "启动前端服务..."
    python3 scripts/start_frontend.py &
    FRONTEND_PID=$!

    log_success "前端服务已启动 (PID: $FRONTEND_PID)"

    echo "=================================================="
    log_success "🎉 IntelliSearch 服务启动完成!"
    echo ""
    echo "🌐 前端地址: http://localhost:3000"
    echo "🚀 后端API: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
    echo ""
    echo "💡 使用说明:"
    echo "   - 在浏览器中打开 http://localhost:3000"
    echo "   - 开始与AI助手对话"
    echo "   - 支持工具调用功能和酷炫特效"
    echo ""
    echo "🛑 停止服务: 按 Ctrl+C"
    echo ""

    # 创建PID文件
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"
    echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"

    # 等待用户中断
    cleanup() {
        log_info "正在停止服务..."

        if [ -f "$PROJECT_ROOT/.backend.pid" ]; then
            BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
            if kill -0 $BACKEND_PID 2>/dev/null; then
                kill $BACKEND_PID
                log_info "后端服务已停止"
            fi
            rm -f "$PROJECT_ROOT/.backend.pid"
        fi

        if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
            FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                kill $FRONTEND_PID
                log_info "前端服务已停止"
            fi
            rm -f "$PROJECT_ROOT/.frontend.pid"
        fi

        log_success "所有服务已停止"
        exit 0
    }

    # 捕获中断信号
    trap cleanup SIGINT SIGTERM

    # 等待
    wait
}

# 主函数
main() {
    echo "🤖 IntelliSearch 全服务启动脚本"
    echo "=================================================="

    check_config
    install_dependencies
    create_log_dirs
    start_services
}

# 执行主函数
main "$@"