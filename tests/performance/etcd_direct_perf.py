import time
import etcd3
import os
import threading
import random
import string
import statistics
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EtcdPerf")

# Configuration
ETCD_HOST = os.getenv("ETCD_HOST", "100.101.75.66")
ETCD_PORT = int(os.getenv("ETCD_PORT", 2379))
NUM_OPERATIONS = int(os.getenv("PERF_OPS", 100))
CONCURRENCY = int(os.getenv("PERF_CONCURRENCY", 10))
DATA_SIZE = int(os.getenv("PERF_DATA_SIZE", 1024)) # 1KB

def get_client():
    return etcd3.client(host=ETCD_HOST, port=ETCD_PORT)

def generate_value(size):
    return ''.join(random.choices(string.ascii_letters, k=size))

def benchmark_op(name, op_func, count, concurrency=1):
    logger.info(f"Starting benchmark: {name} (Ops: {count}, Concurrency: {concurrency})")
    latencies = []
    errors = 0
    
    start_time = time.time()
    
    def worker(num_ops):
        local_latencies = []
        local_errors = 0
        client = get_client()
        for i in range(num_ops):
            op_start = time.time()
            try:
                op_func(client, i)
                local_latencies.append(time.time() - op_start)
            except Exception as e:
                local_errors += 1
                logger.error(f"Error in {name}: {e}")
        return local_latencies, local_errors

    threads = []
    ops_per_thread = count // concurrency
    results = []
    
    for _ in range(concurrency):
        t = threading.Thread(target=lambda: results.append(worker(ops_per_thread)))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    for res in results:
        latencies.extend(res[0])
        errors += res[1]
        
    total_time = time.time() - start_time
    
    if not latencies:
        logger.error(f"No successful operations for {name}")
        return

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
    throughput = len(latencies) / total_time
    
    print(f"\n--- Results for {name} ---")
    print(f"Total Time: {total_time:.4f}s")
    print(f"Total Ops: {len(latencies)}")
    print(f"Errors: {errors}")
    print(f"Throughput: {throughput:.2f} ops/sec")
    print(f"Avg Latency: {avg_latency*1000:.2f} ms")
    print(f"P95 Latency: {p95_latency*1000:.2f} ms")
    print(f"P99 Latency: {p99_latency*1000:.2f} ms")
    print("--------------------------\n")

def run_benchmarks():
    print(f"Connecting to etcd at {ETCD_HOST}:{ETCD_PORT}")
    val = generate_value(DATA_SIZE)
    
    # Define operations
    def write_op(client, i):
        client.put(f"/perf/key-{i}", val)
        
    def read_op(client, i):
        client.get(f"/perf/key-{i}")
        
    # 1. Sequential Write
    benchmark_op("Sequential Write", write_op, NUM_OPERATIONS, 1)
    
    # 2. Sequential Read
    benchmark_op("Sequential Read", read_op, NUM_OPERATIONS, 1)
    
    # 3. Concurrent Write
    benchmark_op("Concurrent Write", write_op, NUM_OPERATIONS, CONCURRENCY)
    
    # 4. Concurrent Read
    benchmark_op("Concurrent Read", read_op, NUM_OPERATIONS, CONCURRENCY)

if __name__ == "__main__":
    run_benchmarks()
