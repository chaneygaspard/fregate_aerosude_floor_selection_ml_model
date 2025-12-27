#!/bin/bash
# SSH Tunnel Setup Script for RTLS Data Collection
# This script starts the required SSH tunnels for the ML data generation

echo "🚀 Starting SSH tunnels for RTLS data collection..."

# Function to start tunnel in background
start_tunnel() {
    local name=$1
    local local_port=$2
    local remote_port=$3
    local server=$4
    local user=$5
    local key=$6
    
    echo "🔗 Starting $name tunnel (local:$local_port -> remote:$remote_port)..."
    
    # Check if tunnel is already running
    if netstat -tlnp 2>/dev/null | grep -q ":$local_port "; then
        echo "⚠️  Port $local_port is already in use. Skipping $name tunnel."
        return 1
    fi
    
    # Start tunnel in background
    ssh -i "$key" -N -L "127.0.0.1:$local_port:127.0.0.1:$remote_port" -p 22 "$user@$server" &
    local tunnel_pid=$!
    
    # Wait a moment and check if tunnel started successfully
    sleep 2
    if kill -0 $tunnel_pid 2>/dev/null; then
        echo "✅ $name tunnel started (PID: $tunnel_pid)"
        echo "$tunnel_pid" > "/tmp/rtls_${name}_tunnel.pid"
        return 0
    else
        echo "❌ Failed to start $name tunnel"
        return 1
    fi
}

# Configuration
SSH_KEY=""  # SSH key path (redacted)
SERVER1=""  # Server 1 address (redacted)
SERVER2=""  # Server 2 address (redacted)
USER1=""  # Server 1 username (redacted)
USER2=""  # Server 2 username (redacted)

# Start tunnels
echo "📡 Setting up tunnels to $SERVER1..."
start_tunnel "api" 8443 8443 "$SERVER1" "$USER1" "$SSH_KEY"  # API runs on 8443 on server
start_tunnel "mqtt" 1884 1885 "$SERVER1" "$USER1" "$SSH_KEY"  # MQTT runs on 1885 on server

echo ""
echo "📡 Setting up tunnels to $SERVER2..."
start_tunnel "api2" 8444 443 "$SERVER2" "$USER2" "$SSH_KEY"
start_tunnel "mqtt2" 1885 1885 "$SERVER2" "$USER2" "$SSH_KEY"

echo ""
echo "🔍 Checking tunnel status..."
sleep 3

# Check tunnel status
for port in 8443 1884 8444 1885; do
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✅ Port $port is active"
    else
        echo "❌ Port $port is not active"
    fi
done

echo ""
echo "📋 Tunnel PIDs saved to:"
echo "   /tmp/rtls_api_tunnel.pid"
echo "   /tmp/rtls_mqtt_tunnel.pid"
echo "   /tmp/rtls_api2_tunnel.pid"
echo "   /tmp/rtls_mqtt2_tunnel.pid"
echo ""
echo "🛑 To stop tunnels, run: ./stop_tunnels.sh"
echo "🚀 You can now run: python3 generate_ml_data_exte.py"
