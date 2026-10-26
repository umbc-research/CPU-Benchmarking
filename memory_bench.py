import time
import os
import platform
import json
import numpy as np

def run_stream_benchmark(array_size=80000000, iterations=10):
    node_name = platform.node()
    cpu_count = os.cpu_count()
    
    print("==================================================")
    print(f" HPC MEMORY (STREAM) BENCHMARK")
    print(f" Node: {node_name}")
    print(f" CPU Cores: {cpu_count}")
    print(f" Array Size: {array_size:,} float64 elements (~{round(array_size * 8 / 1e6, 2)} MB / array)")
    print("==================================================\n")

    # Allocate 3 arrays (~1.92 GB total)
    print("Allocating memory arrays...")
    a = np.ones(array_size, dtype=np.float64)
    b = np.ones(array_size, dtype=np.float64) * 2.0
    c = np.zeros(array_size, dtype=np.float64)
    scalar = 3.0

    # Bytes transferred per kernel operation
    # Copy: 2 arrays (Read A, Write C) -> 2 * size * 8
    # Scale: 2 arrays (Read C, Write B) -> 2 * size * 8
    # Add: 3 arrays (Read A, Read B, Write C) -> 3 * size * 8
    # Triad: 3 arrays (Read B, Read C, Write A) -> 3 * size * 8
    bytes_copy = 2.0 * array_size * 8
    bytes_scale = 2.0 * array_size * 8
    bytes_add = 3.0 * array_size * 8
    bytes_triad = 3.0 * array_size * 8

    # Warm-up pass
    print("Warming up memory and threads...")
    c[:] = a[:]

    times_copy, times_scale, times_add, times_triad = [], [], [], []

    print(f"Executing {iterations} STREAM iterations...")
    for i in range(iterations):
        # 1. Copy
        t0 = time.perf_counter()
        c[:] = a[:]
        t1 = time.perf_counter()
        times_copy.append(t1 - t0)

        # 2. Scale
        t0 = time.perf_counter()
        b[:] = scalar * c[:]
        t1 = time.perf_counter()
        times_scale.append(t1 - t0)

        # 3. Add
        t0 = time.perf_counter()
        c[:] = a[:] + b[:]
        t1 = time.perf_counter()
        times_add.append(t1 - t0)

        # 4. Triad
        t0 = time.perf_counter()
        a[:] = b[:] + scalar * c[:]
        t1 = time.perf_counter()
        times_triad.append(t1 - t0)

    # Calculate best bandwidth (GB/s) per STREAM specification
    bw_copy = round((bytes_copy / min(times_copy)) / 1e9, 2)
    bw_scale = round((bytes_scale / min(times_scale)) / 1e9, 2)
    bw_add = round((bytes_add / min(times_add)) / 1e9, 2)
    bw_triad = round((bytes_triad / min(times_triad)) / 1e9, 2)

    results = {
        "node": node_name,
        "cores": cpu_count,
        "copy_gbps": bw_copy,
        "scale_gbps": bw_scale,
        "add_gbps": bw_add,
        "triad_gbps": bw_triad
    }

    print("\n--------------------------------------------------")
    print(f" RESULT SUMMARY FOR {node_name}")
    print(f" Copy Bandwidth:  {bw_copy} GB/s")
    print(f" Scale Bandwidth: {bw_scale} GB/s")
    print(f" Add Bandwidth:   {bw_add} GB/s")
    print(f" Triad Bandwidth: {bw_triad} GB/s")
    print("--------------------------------------------------\n")

    out_file = f"memory_{node_name}.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON metrics to {out_file}")

if __name__ == "__main__":
    run_stream_benchmark()
