#!/bin/bash

# ==============================================
#   Minimal IntelliSearch Service Manager
# ==============================================

# Service definitions: name="port|command"
declare -A SERVICES
SERVICES[local_sai]="39255|python mcp_server/local_sai_search/rag_service.py"
SERVICES[ipython_backend]="39256|python mcp_server/python_executor/ipython_backend.py"

check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -t -i :$port 2>/dev/null
    else
        netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1
    fi
}

start_services() {
    mkdir -p log
    for svc in "${!SERVICES[@]}"; do
        IFS='|' read -r port cmd <<< "${SERVICES[$svc]}"

        pid=$(check_port "$port")
        if [ -n "$pid" ]; then
            echo "Port $port is occupied (PID: $pid). Kill it? [y/N]"
            read -r ans
            if [[ "$ans" =~ ^[Yy]$ ]]; then
                kill "$pid" 2>/dev/null || kill -9 "$pid"
                sleep 1
            else
                echo "Skipping $svc."
                continue
            fi
        fi

        echo "Starting $svc on port $port"
        nohup $cmd > "log/${svc}.log" 2>&1 &
        sleep 1
    done
}

status_services() {
    for svc in "${!SERVICES[@]}"; do
        IFS='|' read -r port cmd <<< "${SERVICES[$svc]}"
        pid=$(check_port "$port")
        if [ -n "$pid" ]; then
            echo "$svc RUNNING (PID: $pid, Port: $port)"
        else
            echo "$svc STOPPED (Port: $port)"
        fi
    done
}

stop_services() {
    for svc in "${!SERVICES[@]}"; do
        IFS='|' read -r port cmd <<< "${SERVICES[$svc]}"
        pid=$(check_port "$port")
        if [ -n "$pid" ]; then
            echo "Stopping $svc (PID: $pid)"
            kill "$pid" 2>/dev/null || kill -9 "$pid"
        fi
    done
}

# ==============================================
# Main entry
# ==============================================
case "$1" in
    status)
        status_services
        ;;
    stop)
        stop_services
        ;;
    "" )
        start_services
        ;;
    *)
        echo "Unknown command. Use: <empty> | status | stop"
        exit 1
        ;;
esac
