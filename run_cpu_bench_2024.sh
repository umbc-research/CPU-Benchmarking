#!/bin/bash
#SBATCH --job-name=cpu_bench
#SBATCH --output=./output/cpu_bench_%j.out
#SBATCH --error=./output/cpu_bench_%j.err
#SBATCH --cluster=chip-cpu
#SBATCH --nodes=1
#SBATCH --partition=2024
#SBATCH --account=pi_gobbert
#SBATCH --qos=shared
#SBATCH --time=00:10:00
#SBATCH --mem=16G

# Set thread counts to match available cores
export OMP_NUM_THREADS=${SLURM_CPUS_ON_NODE:-$(nproc)}
export MKL_NUM_THREADS=$OMP_NUM_THREADS
export OPENBLAS_NUM_THREADS=$OMP_NUM_THREADS

cd $SLURM_SUBMIT_DIR

# Activate virtual environment
source venv/bin/activate

# Execute benchmark
python cpu_bench.py
