#!/bin/bash

# IntelliSearch Service Management Script
# Provides comprehensive service management for all IntelliSearch components

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
declare -A SERVICES
SERVICES[local_sai]="Local SAI Search Service|23225|python mcp_server/local_sai_search/rag_service.py"
SERVICES[ipython_backend]="IPython Backend Server|8889|python mcp_server/python_executor/ipython_backend.py"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to get service info
get_service_info() {
    local service_name=$1
    local service_config="${SERVICES[$service_name]}"
    if [ -z "$service_config" ]; then
        echo ""
        return 1
    fi

    IFS='|' read -r service_name_desc port command <<< "$service_config"
    echo "$service_name_desc|$port|$command"
    return 0
}

# Function to check if service is running
is_service_running() {
    local service_name=$1
    local service_info=$(get_service_info "$service_name")

    if [ -z "$service_info" ]; then
        return 1
    fi

    IFS='|' read -r service_desc port command <<< "$service_info"

    # Check for port usage
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :$port >/dev/null 2>&1
    else
        # Fallback to netstat if lsof is not available
        netstat -tlnp 2>/dev/null | grep ":$port " >/dev/null
    fi
    return $?
}

# Function to get service PID
get_service_pid() {
    local service_name=$1
    local service_info=$(get_service_info "$service_name")

    if [ -z "$service_info" ]; then
        return 1
    fi

    IFS='|' read -r service_desc port command <<< "$service_info"

    # Find PID by port
    if command -v lsof >/dev/null 2>&1; then
        lsof -t -i :$port 2>/dev/null
    else
        # Fallback method using netstat and ps
        netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_info=$(get_service_info "$service_name")

    if [ -z "$service_info" ]; then
        print_status $RED "Error: Unknown service '$service_name'"
        return 1
    fi

    IFS='|' read -r service_desc port command <<< "$service_info"

    if is_service_running "$service_name"; then
        print_status $YELLOW "$service_desc is already running (port: $port)"
        return 0
    fi

    print_status $BLUE "Starting $service_desc (port: $port)..."

    # Create log directory if it doesn't exist
    mkdir -p log

    # Start service in background with logging
    if [[ "$service_name" == "ipython_mcp" ]]; then
        # MCP server runs directly (no backgrounding)
        $command
    else
        # Backend services run in background
        echo "Running Command: $command"
        nohup $command > "log/${service_name}.log" 2>&1 &
        local pid=$!

        # Wait a moment for service to start
        sleep 2

        if is_service_running "$service_name"; then
            print_status $GREEN "✅ $service_desc started successfully (PID: $pid)"
            echo $pid > "log/service_${service_name}.pid"
        else
            print_status $RED "❌ Failed to start $service_desc"
            return 1
        fi
    fi

    return 0
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local service_info=$(get_service_info "$service_name")

    if [ -z "$service_info" ]; then
        print_status $RED "Error: Unknown service '$service_name'"
        return 1
    fi

    IFS='|' read -r service_desc port command <<< "$service_info"

    if ! is_service_running "$service_name"; then
        print_status $YELLOW "$service_desc is not running"
        return 0
    fi

    print_status $BLUE "Stopping $service_desc..."

    local pid=$(get_service_pid "$service_name")

    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        kill $pid
        sleep 1

        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            kill -9 $pid
            sleep 1
        fi

        print_status $GREEN "✅ $service_desc stopped"
    else
        print_status $YELLOW "$service_desc was not running"
    fi

    # Clean up PID file
    [ -f "logs/${service_name}.pid" ] && rm -f "logs/${service_name}.pid"

    return 0
}

# Function to restart a service
restart_service() {
    local service_name=$1
    stop_service "$service_name"
    sleep 2
    start_service "$service_name"
}

# Function to check service status
check_status() {
    print_status $BLUE "IntelliSearch Service Status:"
    echo "================================"

    for service_name in "${!SERVICES[@]}"; do
        local service_info=$(get_service_info "$service_name")
        IFS='|' read -r service_desc port command <<< "$service_info"

        if is_service_running "$service_name"; then
            local pid=$(get_service_pid "$service_name")
            print_status $GREEN "✅ $service_desc: RUNNING (PID: $pid, Port: $port)"
        else
            print_status $RED "❌ $service_desc: STOPPED (Port: $port)"
        fi
    done

    echo ""
}

# Function to show logs
show_logs() {
    local service_name=$1
    local follow=$2
    local service_info=$(get_service_info "$service_name")

    if [ -z "$service_info" ]; then
        print_status $RED "Error: Unknown service '$service_name'"
        print_status $BLUE "Available services: ${!SERVICES[*]}"
        return 1
    fi

    local log_file="log/${service_name}.log"

    if [ ! -f "$log_file" ]; then
        print_status $YELLOW "No log file found for $service_name"
        return 0
    fi

    if [ "$follow" == "true" ]; then
        tail -f "$log_file"
    else
        tail -n 50 "$log_file"
    fi
}

# Function to show help
show_help() {
    print_status $BLUE "IntelliSearch Service Manager"
    echo "Usage: $0 {start|stop|restart|status|logs|help} [service_name] [options]"
    echo ""
    echo "Commands:"
    echo "  start [service]     Start all services or specific service"
    echo "  stop [service]      Stop all services or specific service"
    echo "  restart [service]   Restart all services or specific service"
    echo "  status              Show status of all services"
    echo "  logs <service>      Show logs for specific service"
    echo "  logs <service> --follow  Follow log output in real-time"
    echo "  help                Show this help message"
    echo ""
    echo "Available services:"
    for service_name in "${!SERVICES[@]}"; do
        local service_info=$(get_service_info "$service_name")
        IFS='|' read -r service_desc port command <<< "$service_info"
        echo "  - $service_name: $service_desc (port: $port)"
    done
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 start ipython_backend    # Start only IPython backend"
    echo "  $0 stop local_sai           # Stop Local SAI search"
    echo "  $0 logs ipython_backend     # Show IPython backend logs"
    echo "  $0 logs ipython_backend --follow  # Follow logs"
}

# Main script logic
case "${1:-}" in
    start)
        if [ -z "$2" ]; then
            print_status $BLUE "Starting all IntelliSearch services..."
            for service_name in "${!SERVICES[@]}"; do
                start_service "$service_name"
            done
            print_status $GREEN "All services started! Check status with: $0 status"
        else
            start_service "$2"
        fi
        ;;
    stop)
        if [ -z "$2" ]; then
            print_status $BLUE "Stopping all IntelliSearch services..."
            for service_name in "${!SERVICES[@]}"; do
                stop_service "$service_name"
            done
            print_status $GREEN "All services stopped!"
        else
            stop_service "$2"
        fi
        ;;
    restart)
        if [ -z "$2" ]; then
            print_status $BLUE "Restarting all IntelliSearch services..."
            for service_name in "${!SERVICES[@]}"; do
                restart_service "$service_name"
            done
            print_status $GREEN "All services restarted!"
        else
            restart_service "$2"
        fi
        ;;
    status)
        check_status
        ;;
    logs)
        if [ -z "$2" ]; then
            print_status $RED "Error: Please specify a service name"
            print_status $BLUE "Available services: ${!SERVICES[*]}"
            exit 1
        fi

        local follow_flag="false"
        if [ "$3" == "--follow" ]; then
            follow_flag="true"
        fi

        show_logs "$2" "$follow_flag"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        print_status $YELLOW "No command specified. Use '$0 help' for usage information."
        show_help
        ;;
    *)
        print_status $RED "Error: Unknown command '$1'"
        print_status $BLUE "Use '$0 help' for usage information"
        exit 1
        ;;
esac