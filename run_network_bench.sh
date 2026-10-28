#!/bin/bash
#SBATCH --job-name=net_bench
#SBATCH --output=net_bench_%j.out
#SBATCH --error=net_bench_%j.err
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

# Get server node hostname (the first node in the allocated list)
SERVER_NODE=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -n 1)

# Activate virtual environment
source venv/bin/activate

# Execute network benchmark across both nodes simultaneously
srun python network_bench.py $SERVER_NODE
