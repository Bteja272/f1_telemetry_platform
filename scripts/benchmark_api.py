import statistics
import time

import requests


BASE_URL = "http://127.0.0.1:8000"


def measure_endpoint(path: str, runs: int = 20):
    latencies = []

    for _ in range(runs):
        start = time.perf_counter()
        response = requests.get(f"{BASE_URL}{path}", timeout=10)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        latencies.append(elapsed_ms)

    return {
        "endpoint": path,
        "runs": runs,
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "p95_latency_ms": round(statistics.quantiles(latencies, n=20)[18], 2),
    }


def main():
    results = [
        measure_endpoint("/drivers/1/latest"),
        measure_endpoint("/drivers/1/history?limit=50"),
        measure_endpoint("/metrics/system"),
    ]

    for result in results:
        print(result)


if __name__ == "__main__":
    main()