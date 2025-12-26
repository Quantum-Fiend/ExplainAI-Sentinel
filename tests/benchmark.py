import time
import requests
import statistics
import concurrent.futures

# Target URL (Logging or AI Engine for intensity)
URL = "http://localhost:8001/detect"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 100

PAYLOAD = {
    "event_id": "bench-test",
    "features": {"f1": 0.5, "f2": 0.5},
    "metadata": {"source": "benchmark"}
}

def send_request():
    start = time.time()
    try:
        resp = requests.post(URL, json=PAYLOAD, timeout=5)
        latency = (time.time() - start) * 1000 # ms
        return resp.status_code, latency
    except Exception as e:
        return 500, 0

def run_benchmark():
    print(f"🚀 Starting Benchmark: {TOTAL_REQUESTS} requests, Concurrency={CONCURRENT_REQUESTS}")
    
    latencies = []
    success_count = 0
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(send_request) for _ in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            status, latency = future.result()
            if status == 200:
                success_count += 1
                latencies.append(latency)
    
    total_time = time.time() - start_time
    
    if latencies:
        print("\n📊 Benchmark Results:")
        print(f"Total Time: {total_time:.2f} s")
        print(f"Success Rate: {success_count}/{TOTAL_REQUESTS} ({(success_count/TOTAL_REQUESTS)*100}%)")
        print(f"Throughput: {success_count/total_time:.2f} req/s")
        print(f"Average Latency: {statistics.mean(latencies):.2f} ms")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f} ms") # P95
    else:
        print("❌ All requests failed. Ensure the target service is running.")

if __name__ == "__main__":
    run_benchmark()
