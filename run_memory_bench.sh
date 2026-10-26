#!/bin/bash
#SBATCH --job-name=memory_bench
#SBATCH --output=memory_bench_%j.out
#SBATCH --error=memory_bench_%j.err
#SBATCH --cluster=chip-cpu
#SBATCH --nodes=1
#SBATCH --partition=general
#SBATCH --account=pi_doit
#SBATCH --qos=normal
#SBATCH --time=00:05:00
#SBATCH --mem=16G

# Ensure openmp/mkl threads utilize all cores allocated to the job
export OMP_NUM_THREADS=${SLURM_CPUS_ON_NODE:-$(nproc)}
export MKL_NUM_THREADS=$OMP_NUM_THREADS
export OPENBLAS_NUM_THREADS=$OMP_NUM_THREADS

cd $SLURM_SUBMIT_DIR

# Activate virtual environment
source venv/bin/activate

# Execute memory benchmark
python memory_bench.py
