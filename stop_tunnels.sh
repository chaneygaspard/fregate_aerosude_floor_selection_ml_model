#!/bin/bash
# Stop SSH Tunnels Script

echo "🛑 Stopping SSH tunnels..."

# Function to stop tunnel by PID file
stop_tunnel() {
    local name=$1
    local pid_file="/tmp/rtls_${name}_tunnel.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🛑 Stopping $name tunnel (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
            echo "✅ $name tunnel stopped"
        else
            echo "⚠️  $name tunnel (PID: $pid) was not running"
            rm "$pid_file"
        fi
    else
        echo "⚠️  No PID file found for $name tunnel"
    fi
}

# Stop all tunnels
stop_tunnel "api"
stop_tunnel "mqtt"
stop_tunnel "api2"
stop_tunnel "mqtt2"

echo ""
echo "🔍 Checking for remaining tunnel processes..."
remaining=$(ps aux | grep "ssh.*-L.*127.0.0.1" | grep -v grep | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo "⚠️  Found $remaining remaining SSH tunnel processes:"
    ps aux | grep "ssh.*-L.*127.0.0.1" | grep -v grep
    echo ""
    echo "💡 To stop them manually: kill <PID>"
else
    echo "✅ All tunnels stopped"
fi
