#!/bin/bash
#SBATCH --job-name=net_omb
#SBATCH --output=output/network_bench_%j.out
#SBATCH --error=output/network_bench_%j.err
#SBATCH --cluster=chip-cpu
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=1
#SBATCH --partition=general
#SBATCH --account=pi_doit
#SBATCH --qos=normal
#SBATCH --time=00:05:00
#SBATCH --mem=8G

cd $SLURM_SUBMIT_DIR

# Load OpenMPI environment module
module load OpenMPI/4.1.6-GCC-13.2.0

# Activate virtual environment
source venv/bin/activate

# Execute Python wrapper around OSU Micro-Benchmarks
python network_bench.py
