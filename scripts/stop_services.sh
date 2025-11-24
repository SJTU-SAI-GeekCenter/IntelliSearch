#!/bin/bash

# IntelliSearch 停止服务脚本

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

# 停止服务函数
stop_service() {
    local service_name=$1
    local pid_file=$2
    local port=$3

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            log_info "停止 $service_name 服务 (PID: $pid)..."
            kill $pid

            # 等待进程结束
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done

            if kill -0 $pid 2>/dev/null; then
                log_warning "$service_name 服务未正常停止，强制结束..."
                kill -9 $pid
            fi

            log_success "$service_name 服务已停止"
        else
            log_warning "$service_name 服务不存在 (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        # 如果没有PID文件，尝试通过端口杀死进程
        if [ -n "$port" ]; then
            local pid=$(lsof -ti:$port 2>/dev/null || true)
            if [ -n "$pid" ]; then
                log_info "停止 $service_name 服务 (端口: $port, PID: $pid)..."
                kill $pid
                log_success "$service_name 服务已停止"
            else
                log_info "$service_name 服务未运行 (端口: $port)"
            fi
        else
            log_info "$service_name 服务未运行"
        fi
    fi
}

# 主函数
main() {
    echo "🛑 IntelliSearch 停止服务脚本"
    echo "=================================================="

    # 停止后端服务
    stop_service "后端" "$PROJECT_ROOT/.backend.pid" "8000"

    # 停止前端服务
    stop_service "前端" "$PROJECT_ROOT/.frontend.pid" "3000"

    # 清理可能残留的Python进程
    log_info "清理残留进程..."
    pkill -f "uvicorn.*backend.main_fastapi" 2>/dev/null || true
    pkill -f "python.*scripts/start_backend.py" 2>/dev/null || true
    pkill -f "python.*scripts/start_frontend.py" 2>/dev/null || true

    echo "=================================================="
    log_success "🎉 所有服务已停止"
}

# 执行主函数
main "$@"