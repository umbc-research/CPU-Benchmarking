import os
import sys
import subprocess
import json
import re

def run_omb_benchmark():
    slurm_submit_dir = os.environ.get("SLURM_SUBMIT_DIR", os.getcwd())
    omb_dir = os.path.join(slurm_submit_dir, "omb", "libexec", "osu-micro-benchmarks", "mpi", "pt2pt")
    
    latency_bin = os.path.join(omb_dir, "osu_latency")
    bw_bin = os.path.join(omb_dir, "osu_bw")

    if not os.path.exists(latency_bin) or not os.path.exists(bw_bin):
        print(f"ERROR: OMB binaries not found in {omb_dir}. Build OMB first.")
        sys.exit(1)

    node_list = os.environ.get("SLURM_JOB_NODELIST", "unknown")

    # 1. Run OSU Latency
    print("Running OSU Latency Test...")
    cmd_lat = ["mpirun", "--mca", "pml", "ucx", "-np", "2", latency_bin]
    res_lat = subprocess.run(cmd_lat, capture_output=True, text=True)

    latency_us = None
    for line in res_lat.stdout.splitlines():
        # Grab lowest payload size (0 or 8 bytes) for true hardware wire latency
        parts = line.strip().split()
        if len(parts) == 2 and parts[0] in ["0", "8"]:
            try:
                latency_us = float(parts[1])
                break
            except ValueError:
                pass

    # 2. Run OSU Bandwidth
    print("Running OSU Bandwidth Test...")
    cmd_bw = ["mpirun", "--mca", "pml", "ucx", "-np", "2", bw_bin]
    res_bw = subprocess.run(cmd_bw, capture_output=True, text=True)

    peak_bw_mbps = 0.0
    for line in res_bw.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            try:
                bw = float(parts[1])
                if bw > peak_bw_mbps:
                    peak_bw_mbps = bw
            except ValueError:
                pass

    peak_bw_gbps = round((peak_bw_mbps * 8) / 1000.0, 2)

    results = {
        "nodes": node_list,
        "latency_us": latency_us,
        "peak_bandwidth_mbps": peak_bw_mbps,
        "peak_bandwidth_gbps": peak_bw_gbps
    }

    print("\n--------------------------------------------------")
    print(f" OSU MICRO-BENCHMARK RESULTS ({node_list})")
    print(f" Wire Latency (4-byte):   {latency_us} us")
    print(f" Peak Throughput Speed:   {peak_bw_mbps} MB/s ({peak_bw_gbps} Gbps)")
    print("--------------------------------------------------\n")

    out_file = "network_omb_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON metrics to {out_file}")

if __name__ == "__main__":
    run_omb_benchmark()
