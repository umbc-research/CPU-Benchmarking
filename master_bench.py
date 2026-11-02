import argparse
import subprocess
import itertools
import logging
import json
import os
import shutil
import concurrent.futures
from datetime import datetime

def setup_loggers(timestamp):
    os.makedirs("output", exist_ok=True)
    
    full_logger = logging.getLogger("FullLog")
    full_logger.setLevel(logging.DEBUG)
    full_logger.addHandler(logging.FileHandler(f"output/bench_full_{timestamp}.log"))

    simple_logger = logging.getLogger("SimpleLog")
    simple_logger.setLevel(logging.INFO)
    simple_logger.addHandler(logging.FileHandler(f"output/bench_simple_{timestamp}.log"))
    simple_logger.addHandler(logging.StreamHandler())

    return simple_logger, full_logger

def run_sbatch_wait(cmd, full_logger, description):
    """Runs sbatch --wait and captures stdout/stderr."""
    full_logger.debug(f"\n{'='*50}\n[START] {description}\nCMD: {' '.join(cmd)}")
    try:
        # Capture the job ID to know which JSON file to look for
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        full_logger.debug(result.stdout)
        full_logger.debug(f"[END] {description} - Exit: {result.returncode}\n{'='*50}")
        
        # Extract the Slurm Job ID from stdout (e.g., "Submitted batch job 12345")
        job_id = "unknown"
        for line in result.stdout.splitlines():
            if "Submitted batch job" in line:
                job_id = line.split()[-1]
                
        return result.returncode, job_id
    except Exception as e:
        full_logger.error(f"[SYSTEM ERROR] {description}: {str(e)}")
        return -1, "unknown"

def safe_read_json(filepath, dest_archive_path):
    if not os.path.exists(filepath):
        return {"error": f"Output file {filepath} not found. Job crashed or hung."}
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        shutil.move(filepath, dest_archive_path)
        return data
    except Exception as e:
        return {"error": f"Failed to parse {filepath}: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Parallel Master Benchmark Runner")
    parser.add_argument('--nodes', nargs='+', required=True, help="List of nodes to test")
    parser.add_argument('--reservation', type=str, default=None, help="Optional reservation name")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    simple_logger, full_logger = setup_loggers(timestamp)
    
    master_results = {
        "metadata": {"timestamp": timestamp, "reservation": args.reservation or "DRY_RUN", "nodes": args.nodes},
        "cpu_benchmarks": {},
        "network_benchmarks": {}
    }

    base_slurm = ["sbatch", "--wait", "--cluster=chip-cpu", "--partition=support", "--qos=support", "--account=pi_doit"]
    if args.reservation:
        base_slurm.append(f"--reservation={args.reservation}")

    # ==========================================
    # Phase 1: Parallel CPU Benchmarks
    # ==========================================
    simple_logger.info("=== PHASE 1: Parallel CPU Benchmarks ===")
    
    def run_cpu(node):
        cmd = base_slurm + [f"--nodelist={node}", "--job-name=cpu_bench", "run_cpu_bench.sh"]
        code, job_id = run_sbatch_wait(cmd, full_logger, f"CPU Bench on {node}")
        return node, code, job_id

    # Launch all CPU jobs simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.nodes)) as executor:
        futures = [executor.submit(run_cpu, node) for node in args.nodes]
        for future in concurrent.futures.as_completed(futures):
            node, code, job_id = future.result()
            
            expected_json = f"cpu_{node}.json"  # Ensure cpu_bench.py outputs to this!
            archive_json = f"output/cpu_{node}_{timestamp}.json"
            
            node_data = safe_read_json(expected_json, archive_json)
            master_results["cpu_benchmarks"][node] = node_data
            
            if code == 0 and "error" not in node_data:
                simple_logger.info(f"[SUCCESS] {node}: CPU Benchmark complete.")
            else:
                simple_logger.info(f"[FAILED]  {node}: Check logs. Error: {node_data.get('error', 'Crashed')}")

    # ==========================================
    # Phase 2: Parallel Network Matrix
    # ==========================================
    simple_logger.info("\n=== PHASE 2: Parallel Cross-Node Bandwidth Matrix ===")
    if len(args.nodes) < 2:
        simple_logger.info("Skipping Phase 2: Need at least 2 nodes.")
    else:
        node_pairs = list(itertools.combinations(args.nodes, 2))
        
        def run_net(pair):
            src, dest = pair
            # Added --exclusive so Slurm won't overlap jobs on the same node
            cmd = base_slurm + ["--exclusive", f"--nodelist={src},{dest}", "--job-name=net_bench", "run_network_bench.sh"]
            code, job_id = run_sbatch_wait(cmd, full_logger, f"Bandwidth {src} <-> {dest}")
            return src, dest, code, job_id

        # Launch all Network pairs simultaneously. Slurm will handle the non-overlapping scheduling!
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(node_pairs)) as executor:
            futures = [executor.submit(run_net, pair) for pair in node_pairs]
            for future in concurrent.futures.as_completed(futures):
                src, dest, code, job_id = future.result()
                
                # Relies on the network_bench.py job_id fix mentioned above
                expected_json = f"network_omb_{job_id}.json"
                archive_json = f"output/network_{src}_{dest}_{timestamp}.json"
                
                net_data = safe_read_json(expected_json, archive_json)
                master_results["network_benchmarks"][f"{src}_to_{dest}"] = net_data
                
                if code == 0 and "error" not in net_data:
                    gbps = net_data.get("peak_bandwidth_gbps", "Unknown")
                    simple_logger.info(f"[SUCCESS] {src} <-> {dest} : Avg Bandwidth: {gbps} Gbps")
                else:
                    simple_logger.info(f"[FAILED]  {src} <-> {dest} : Error: {net_data.get('error', 'Crashed')}")

    # ==========================================
    # Finalize
    # ==========================================
    master_json_path = f"output/master_results_{timestamp}.json"
    with open(master_json_path, 'w') as f:
        json.dump(master_results, f, indent=2)
    
    simple_logger.info(f"\n=== FINISHED ===")
    simple_logger.info(f"Master JSON saved to: {master_json_path}")

if __name__ == "__main__":
    main()
