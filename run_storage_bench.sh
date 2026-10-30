#!/bin/bash
#SBATCH --job-name=storage_bench
#SBATCH --output=output/storage_bench_%j.out
#SBATCH --error=output/storage_bench_%j.err
#SBATCH --cluster=chip-cpu
#SBATCH --nodes=1
#SBATCH --partition=general
#SBATCH --account=pi_doit
#SBATCH --qos=normal
#SBATCH --time=00:15:00
#SBATCH --mem=16G

cd $SLURM_SUBMIT_DIR

# Load fio if available via environment modules
module load fio 2>/dev/null || true

# Activate virtual environment
source venv/bin/activate

# Execute storage benchmark
python storage_bench.py
