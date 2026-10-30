import os
import sys
import time
import json
import shutil
import platform
import subprocess

# Active Ceph OSD Pools
TARGET_VOLUMES = {
    "ceph_hdd": "/umbc/rs/pi_doit",
    "ceph_nvme": "/umbc/scratch"
}

WORKLOADS = [
    # (name, type, blocksize, filesize, threads)
    ("randread_small_1t", "randread", "4k", "64M", 1),
    ("randwrite_small_1t", "randwrite", "4k", "64M", 1),
    ("randread_large_1t", "randread", "1M", "512M", 1),
    ("randwrite_large_1t", "randwrite", "1M", "512M", 1),
    ("randread_small_2t", "randread", "4k", "64M", 2),
    ("randwrite_small_2t", "randwrite", "4k", "64M", 2),
    ("randread_large_2t", "randread", "1M", "512M", 2),
    ("randwrite_large_2t", "randwrite", "1M", "512M", 2),
    ("randread_small_4t", "randread", "4k", "64M", 4),
    ("randwrite_small_4t", "randwrite", "4k", "64M", 4),
    ("randread_large_4t", "randread", "1M", "512M", 4),
    ("randwrite_large_4t", "randwrite", "1M", "512M", 4),
]

def check_fio_installed():
    if not shutil.which("fio"):
        print("ERROR: 'fio' executable not found in PATH.", file=sys.stderr)
        sys.exit(1)

def run_fio_subtest(volume_path, subtest_name, rw_type, blocksize, filesize, threads, runtime=20):
    user = os.environ.get("USER", "bench_user")
    test_dir = os.path.join(volume_path, f".fio_bench_{user}")
    
    try:
        os.makedirs(test_dir, exist_ok=True)
    except Exception as e:
        print(f"Cannot create test directory in {volume_path}: {e}")
        return 0.0

    test_file = os.path.join(test_dir, f"{subtest_name}.fio")

    cmd = [
        "fio",
        f"--name={subtest_name}",
        f"--filename={test_file}",
        f"--rw={rw_type}",
        f"--bs={blocksize}",
        f"--size={filesize}",
        "--direct=1",
        "--ioengine=sync",
        f"--runtime={runtime}",
        f"--numjobs={threads}",
        "--time_based",
        "--group_reporting",
        "--eta=never",
        "--output-format=json"
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(test_file):
        os.remove(test_file)

    if res.returncode != 0:
        print(f"Warning: fio failed on {volume_path} for {subtest_name}: {res.stderr[:200]}")
        return 0.0

    try:
        data = json.loads(res.stdout)
        jobs = data.get("jobs", [])
        if rw_type == "randread":
            bytes_transferred = sum(j.get("read", {}).get("bw_bytes", 0) for j in jobs)
        else:
            bytes_transferred = sum(j.get("write", {}).get("bw_bytes", 0) for j in jobs)

        # MiB/s calculation matching Greg's exact formula
        mib_per_sec = round((bytes_transferred / 1048576), 2)
        return mib_per_sec
    except Exception as e:
        print(f"Error parsing JSON output for {subtest_name}: {e}")
        return 0.0

def benchmark_volume(vol_key, vol_path, runtime=20):
    print(f"\n--- Profiling Ceph Pool: {vol_key} ({vol_path}) ---")
    if not os.path.exists(vol_path) or not os.access(vol_path, os.W_OK):
        print(f"Skipping {vol_path}: Path does not exist or is not writable by current user.")
        return None

    vol_results = {}
    for name, rw_type, bs, fsize, threads in WORKLOADS:
        print(f"  Running {name} ({rw_type}, bs={bs}, threads={threads})...")
        mib_s = run_fio_subtest(vol_path, name, rw_type, bs, fsize, threads, runtime=runtime)
        vol_results[name] = mib_s
        print(f"    -> Throughput: {mib_s} MiB/s")

    user = os.environ.get("USER", "bench_user")
    test_dir = os.path.join(vol_path, f".fio_bench_{user}")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)

    return vol_results

def main():
    check_fio_installed()
    node_name = platform.node()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    print("==================================================")
    print(f" HPC CEPH OSD STORAGE PROFILER")
    print(f" Node: {node_name}")
    print(f" Timestamp: {timestamp}")
    print("==================================================")

    all_results = {
        "timestamp": timestamp,
        "node": node_name,
        "volumes": {}
    }

    for vol_key, vol_path in TARGET_VOLUMES.items():
        res = benchmark_volume(vol_key, vol_path, runtime=20)
        if res is not None:
            all_results["volumes"][vol_key] = res

    out_file = f"storage_fio_{node_name}.json"
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print("\n==================================================")
    print(f" COMPLETED STORAGE PROFILE FOR {node_name}")
    print(f" Results saved to: {out_file}")
    print("==================================================")

if __name__ == "__main__":
    main()
