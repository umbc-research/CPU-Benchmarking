import argparse
import subprocess
import itertools
import logging
import json
import os
import re
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
    """Executes sbatch --wait and extracts the numeric Slurm Job ID."""
    full_logger.debug(f"\n{'='*50}\n[START] {description}\nCMD: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        full_logger.debug(result.stdout)
        full_logger.debug(f"[END] {description} - Exit: {result.returncode}\n{'='*50}")
        
        job_id = "unknown"
        for line in result.stdout.splitlines():
            match = re.search(r'Submitted batch job (\d+)', line)
            if match:
                job_id = match.group(1)
                break
                
        return result.returncode, job_id
    except Exception as e:
        full_logger.error(f"[SYSTEM ERROR] {description}: {str(e)}")
        return -1, "unknown"

def safe_read_json(filepath):
    """Reads a generated benchmark JSON file directly from disk."""
    if not os.path.exists(filepath):
        return {"error": f"Output file {filepath} not found. Job crashed or failed."}
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"error": f"Failed to parse {filepath}: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Parallel Master Benchmark Runner")
    parser.add_argument('--nodes', nargs='+', required=True, help="List of nodes to test")
    parser.add_argument('--reservation', type=str, default=None, help="Optional Slurm reservation name")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    simple_logger, full_logger = setup_loggers(timestamp)
    
    master_results = {
        "metadata": {
            "timestamp": timestamp, 
            "reservation": args.reservation or "DRY_RUN", 
            "nodes": args.nodes
        },
        "single_node_benchmarks": {node: {} for node in args.nodes},
        "network_benchmarks": {}
    }

    mode = f"RESERVATION: {args.reservation}" if args.reservation else "DRY RUN (No Reservation)"
    simple_logger.info(f"--- Starting Benchmark Suite | Mode: {mode} ---")
    simple_logger.info(f"Target Nodes: {', '.join(args.nodes)}\n")

    base_slurm = ["sbatch", "--wait", "--cluster=chip-cpu", "--partition=support", "--qos=support", "--account=pi_doit"]
    if args.reservation:
        base_slurm.append(f"--reservation={args.reservation}")

    # ==========================================
    # Phase 1: Parallel Single-Node Benchmarks
    # ==========================================
    simple_logger.info("=== PHASE 1: Single-Node Benchmarks (CPU, Memory, Storage) ===")
    
    single_node_tasks = []
    for node in args.nodes:
        single_node_tasks.append((node, "cpu", "run_cpu_bench.sh", f"output/cpu_{node}_"))
        single_node_tasks.append((node, "memory", "run_memory_bench.sh", f"output/memory_{node}_"))
        single_node_tasks.append((node, "storage", "run_storage_bench.sh", f"output/storage_fio_{node}_"))

    def run_single_benchmark(task):
        node, test_type, script_name, prefix = task
        cmd = base_slurm + [f"--nodelist={node}", f"--job-name={test_type}_{node}", script_name]
        code, job_id = run_sbatch_wait(cmd, full_logger, f"{test_type.upper()} Bench on {node}")
        return node, test_type, code, job_id, prefix

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(single_node_tasks)) as executor:
        futures = [executor.submit(run_single_benchmark, task) for task in single_node_tasks]
        for future in concurrent.futures.as_completed(futures):
            node, test_type, code, job_id, prefix = future.result()
            
            target_json = f"{prefix}{job_id}.json"
            data = safe_read_json(target_json)
            master_results["single_node_benchmarks"][node][test_type] = data
            
            if code == 0 and "error" not in data:
                simple_logger.info(f"[SUCCESS] {node} [{test_type.upper()}]: Benchmark completed.")
            else:
                simple_logger.info(f"[FAILED]  {node} [{test_type.upper()}]: Error: {data.get('error', 'Crashed')}")

    # ==========================================
    # Phase 2: Parallel Cross-Node Network Matrix
    # ==========================================
    simple_logger.info("\n=== PHASE 2: Cross-Node Bandwidth Matrix ===")
    if len(args.nodes) < 2:
        simple_logger.info("Skipping Phase 2: Need at least 2 nodes for pairwise network tests.")
    else:
        node_pairs = list(itertools.combinations(args.nodes, 2))
        
        def run_net_benchmark(pair):
            src, dest = pair
            cmd = base_slurm + ["--exclusive", f"--nodelist={src},{dest}", "--job-name=net_bench", "run_network_bench.sh"]
            code, job_id = run_sbatch_wait(cmd, full_logger, f"Bandwidth {src} <-> {dest}")
            return src, dest, code, job_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(node_pairs)) as executor:
            futures = [executor.submit(run_net_benchmark, pair) for pair in node_pairs]
            for future in concurrent.futures.as_completed(futures):
                src, dest, code, job_id = future.result()
                
                target_json = f"output/network_omb_{job_id}.json"
                data = safe_read_json(target_json)
                master_results["network_benchmarks"][f"{src}_to_{dest}"] = data
                
                if code == 0 and "error" not in data:
                    gbps = data.get("peak_bandwidth_gbps", "Unknown")
                    lat = data.get("latency_us", "Unknown")
                    simple_logger.info(f"[SUCCESS] {src} <-> {dest} : Peak BW: {gbps} Gbps | Latency: {lat} us")
                else:
                    simple_logger.info(f"[FAILED]  {src} <-> {dest} : Error: {data.get('error', 'Crashed')}")

    # ==========================================
    # Output Master Results
    # ==========================================
    master_json_path = f"output/master_results_{timestamp}.json"
    with open(master_json_path, 'w') as f:
        json.dump(master_results, f, indent=2)
    
    simple_logger.info(f"\n=== BENCHMARK SUITE COMPLETE ===")
    simple_logger.info(f"Master JSON saved to: {master_json_path}")

if __name__ == "__main__":
    main()
