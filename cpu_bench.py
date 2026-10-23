import time
import os
import platform
import json
import numpy as np

def run_dgemm_benchmark(matrix_size=8000, iterations=5):
    node_name = platform.node()
    cpu_count = os.cpu_count()
    
    print(f"==================================================")
    print(f" HPC CPU DGEMM BENCHMARK")
    print(f" Node: {node_name}")
    print(f" Available CPU Cores: {cpu_count}")
    print(f" Matrix Dimensions: {matrix_size} x {matrix_size}")
    print(f"==================================================\n")

    # Operations for double-precision N x N matrix multiplication = 2 * N^3
    flops_per_iter = 2.0 * (matrix_size ** 3)

    print("Allocating matrices in memory...")
    A = np.random.randn(matrix_size, matrix_size).astype(np.float64)
    B = np.random.randn(matrix_size, matrix_size).astype(np.float64)

    # Warm-up run to spin up CPU frequency and fill cache
    print("Warming up CPU cores...")
    _ = np.dot(A[:1000, :1000], B[:1000, :1000])

    print(f"Executing {iterations} benchmark passes...")
    gflops_list = []
    times = []

    for i in range(iterations):
        start_time = time.perf_counter()
        _ = np.dot(A, B)
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        gflops = (flops_per_iter / elapsed) / 1e9

        times.append(elapsed)
        gflops_list.append(gflops)
        print(f"  Pass {i+1}: {elapsed:.4f} sec | {gflops:.2f} GFLOPS")

    avg_gflops = sum(gflops_list) / len(gflops_list)
    peak_gflops = max(gflops_list)

    results = {
        "node": node_name,
        "cores": cpu_count,
        "matrix_size": matrix_size,
        "avg_gflops": round(avg_gflops, 2),
        "peak_gflops": round(peak_gflops, 2),
        "min_time_sec": round(min(times), 4)
    }

    print("\n--------------------------------------------------")
    print(f" RESULT SUMMARY FOR {node_name}")
    print(f" Average Compute Throughput: {avg_gflops:.2f} GFLOPS")
    print(f" Peak Compute Throughput:    {peak_gflops:.2f} GFLOPS")
    print("--------------------------------------------------\n")

    # Save JSON summary locally
    out_file = f"cpu_{node_name}.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON metrics to {out_file}")

if __name__ == "__main__":
    run_dgemm_benchmark()
