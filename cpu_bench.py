import time
import os
import platform
import json
import numpy as np

def run_dgemm_benchmark(matrix_size=8000, iterations=5):
    node_name = platform.node().split('.')[0]
    cpu_count = os.cpu_count()
    job_id = os.environ.get("SLURM_JOB_ID", "local")

    print(f"==================================================")
    print(f" HPC CPU DGEMM BENCHMARK")
    print(f" Node: {node_name} | Job ID: {job_id}")
    print(f" Available CPU Cores: {cpu_count}")
    print(f" Matrix Dimensions: {matrix_size} x {matrix_size}")
    print(f"==================================================\n")

    flops_per_iter = 2.0 * (matrix_size ** 3)

    print("Allocating matrices in memory...")
    A = np.random.randn(matrix_size, matrix_size).astype(np.float64)
    B = np.random.randn(matrix_size, matrix_size).astype(np.float64)

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
        "job_id": job_id,
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

    os.makedirs("output", exist_ok=True)
    out_file = os.path.join("output", f"cpu_{node_name}_{job_id}.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON metrics to {out_file}")

if __name__ == "__main__":
    run_dgemm_benchmark()
