# EtcdHelper Performance Test Suite

This directory contains a comprehensive performance testing suite for the `etcdHelper` service and the underlying etcd storage system.

## Prerequisites

- Python 3.x
- Node.js (for the application server)
- Pip packages: `locust`, `etcd3`

```bash
pip install locust etcd3
```

## Structure

- `locustfile.py`: Locust test script defining API user behaviors (GET, PUT, DELETE).
- `etcd_direct_perf.py`: Python script for direct benchmarking of the etcd storage using `etcd3` library.
- `run_tests.sh`: Orchestration script to run the full suite.
- `reports/`: Directory where test reports (CSV, HTML, logs) are generated.

## Running the Tests

Execute the master script:

```bash
./run_tests.sh
```

This script will:
1. Start the `index.js` server in the background.
2. Run direct etcd benchmarks (Sequential/Concurrent Read/Write).
3. Run Locust API tests under Low, Medium, and High load scenarios.
4. Generate CSV and HTML reports in `tests/performance/reports/`.
5. Clean up the server process.

## Test Scenarios

### 1. Direct Etcd Storage Performance
- **Tool**: Custom Python script (`etcd_direct_perf.py`)
- **Metrics**: Throughput (ops/sec), Latency (Avg, P95, P99)
- **Scenarios**:
  - Sequential Write (100 ops)
  - Sequential Read (100 ops)
  - Concurrent Write (100 ops, 10 threads)
  - Concurrent Read (100 ops, 10 threads)

### 2. API Interface Performance
- **Tool**: Locust
- **Metrics**: Requests/sec, Response Time, Failure Rate
- **Scenarios**:
  - **Low Load**: 10 users, spawn rate 2
  - **Medium Load**: 50 users, spawn rate 5
  - **High Load**: 100 users, spawn rate 10
- **Tasks**:
  - GET /kv/:key (Weight: 10)
  - PUT /kv (Weight: 3)
  - DELETE /kv/:key (Weight: 1)

## Interpreting Results

Check the `reports/` directory for:
- `etcd_direct_perf.txt`: Raw output of direct storage benchmarks.
- `locust_*_load.html`: Interactive HTML graphs of API performance.
- `locust_*_load_stats.csv`: Detailed statistics table.

### Key Metrics to Watch
- **Throughput**: If API throughput << Direct Etcd throughput, the bottleneck is likely in the Node.js application or network overhead.
- **P99 Latency**: High P99 spikes indicate instability or resource exhaustion under load.
- **Error Rate**: Any non-zero error rate (excluding 404s for missing keys) indicates system failure.
