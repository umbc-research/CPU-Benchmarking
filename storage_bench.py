import os
import time
import mmap
import json
import platform
import sys

def run_storage_benchmark(test_dir="/tmp", size_mb=1024, block_size_mb=1):
    node_name = platform.node()
    test_file = os.path.join(test_dir, f"speedtest_{node_name}.img")
    
    block_bytes = block_size_mb * 1024 * 1024
    total_bytes = size_mb * 1024 * 1024
    num_blocks = total_bytes // block_bytes

    print("==================================================")
    print(f" HPC NATIVE STORAGE BENCHMARK (O_DIRECT)")
    print(f" Node: {node_name}")
    print(f" Target Path: {test_dir}")
    print(f" Test File Size: {size_mb} MB")
    print("==================================================\n")

    # Allocate 4KB-aligned memory buffer using mmap
    buf = mmap.mmap(-1, block_bytes)
    buf.write(b"A" * block_bytes)

    # 1. Direct Sequential Write Test
    print("Executing Direct Write Test...")
    flags_write = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_DIRECT"):
        flags_write |= os.O_DIRECT

    start_write = time.perf_counter()
    fd = os.open(test_file, flags_write, 0o666)
    for _ in range(num_blocks):
        os.write(fd, buf)
    os.close(fd)
    end_write = time.perf_counter()

    write_elapsed = end_write - start_write
    write_mbps = round(size_mb / write_elapsed, 2)

    # 2. Direct Sequential Read Test
    print("Executing Direct Read Test...")
    flags_read = os.O_RDONLY
    if hasattr(os, "O_DIRECT"):
        flags_read |= os.O_DIRECT

    start_read = time.perf_counter()
    fd = os.open(test_file, flags_read)
    for _ in range(num_blocks):
        _ = os.write(1, b"") if os.read(fd, block_bytes) else None
    os.close(fd)
    end_read = time.perf_counter()

    read_elapsed = end_read - start_read
    read_mbps = round(size_mb / read_elapsed, 2)

    # Clean up file
    if os.path.exists(test_file):
        os.remove(test_file)

    results = {
        "node": node_name,
        "target_dir": test_dir,
        "seq_write_mbps": write_mbps,
        "seq_read_mbps": read_mbps
    }

    print("\n--------------------------------------------------")
    print(f" RESULT SUMMARY FOR {node_name}")
    print(f" Direct Write Throughput: {write_mbps} MB/s")
    print(f" Direct Read Throughput:  {read_mbps} MB/s")
    print("--------------------------------------------------\n")

    out_file = f"storage_{node_name}.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON metrics to {out_file}")

if __name__ == "__main__":
    target_path = os.environ.get("SLURM_TMPDIR", "/tmp")
    run_storage_benchmark(test_dir=target_path)
