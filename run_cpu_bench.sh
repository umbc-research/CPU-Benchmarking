#!/bin/bash
#SBATCH --job-name=cpu_bench
#SBATCH --output=cpu_bench_%j.out
#SBATCH --error=cpu_bench_%j.err
#SBATCH --cluster=chip-cpu
#SBATCH --nodes=1
#SBATCH --partition=general
#SBATCH --account=pi_doit
#SBATCH --qos=normal
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
