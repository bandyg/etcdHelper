#!/bin/bash

# Configuration
SERVICE_DIR="/home/bandyg/services/etcdHelper"
TEST_DIR="$SERVICE_DIR/tests/performance"
REPORT_DIR="$TEST_DIR/reports"
SERVER_PORT=5001
HOST_URL="http://localhost:$SERVER_PORT"

mkdir -p "$REPORT_DIR"

echo "==========================================="
echo "Starting Performance Test Suite"
echo "==========================================="

# 1. Start the API Server
echo "[INFO] Starting etcdHelper API server..."
cd "$SERVICE_DIR"
# Kill existing instance if any
pkill -f "node index.js" || true
nohup node index.js > "$REPORT_DIR/server.log" 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "[INFO] Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s "$HOST_URL/kv/health_check" > /dev/null || curl -s "$HOST_URL/kv/test" > /dev/null; then
        echo "[INFO] Server is up!"
        break
    fi
    sleep 1
done

# 2. Run Direct Etcd Benchmarks
echo ""
echo "==========================================="
echo "Running Direct Etcd Storage Performance Tests"
echo "==========================================="
echo "[INFO] Executing Python benchmark script..."
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
python3 "$TEST_DIR/etcd_direct_perf.py" > "$REPORT_DIR/etcd_direct_perf.txt"
cat "$REPORT_DIR/etcd_direct_perf.txt"

# 3. Run API Performance Tests with Locust
echo ""
echo "==========================================="
echo "Running API Interface Performance Tests (Locust)"
echo "==========================================="

# Low Load
echo "[INFO] Starting Low Load Test (10 users, spawn rate 2, 30s)..."
locust -f "$TEST_DIR/locustfile.py" \
    --headless \
    --host="$HOST_URL" \
    --users 10 \
    --spawn-rate 2 \
    --run-time 30s \
    --csv="$REPORT_DIR/locust_low_load" \
    --html="$REPORT_DIR/locust_low_load.html"

# Medium Load
echo "[INFO] Starting Medium Load Test (50 users, spawn rate 5, 30s)..."
locust -f "$TEST_DIR/locustfile.py" \
    --headless \
    --host="$HOST_URL" \
    --users 50 \
    --spawn-rate 5 \
    --run-time 30s \
    --csv="$REPORT_DIR/locust_medium_load" \
    --html="$REPORT_DIR/locust_medium_load.html"

# High Load
echo "[INFO] Starting High Load Test (100 users, spawn rate 10, 30s)..."
locust -f "$TEST_DIR/locustfile.py" \
    --headless \
    --host="$HOST_URL" \
    --users 100 \
    --spawn-rate 10 \
    --run-time 30s \
    --csv="$REPORT_DIR/locust_high_load" \
    --html="$REPORT_DIR/locust_high_load.html"

# 4. Cleanup
echo ""
echo "==========================================="
echo "Cleaning up..."
kill $SERVER_PID
echo "[INFO] Server stopped."
echo "[INFO] Reports generated in $REPORT_DIR"
echo "==========================================="
