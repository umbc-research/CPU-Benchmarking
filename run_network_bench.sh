#!/bin/bash
#SBATCH --job-name=net_mpi
#SBATCH --output=./output/network_bench_%j.out
#SBATCH --error=./output/network_bench_%j.err
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

# Load system MPI module if required on your cluster (e.g., module load openmpi)
# module load openmpi

source venv/bin/activate

srun python network_bench.py
