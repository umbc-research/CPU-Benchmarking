#!/bin/bash

#SBATCH --job-name=power                # Job name
#SBATCH --output=slurm_%j.out           # Output file name
#SBATCH --error=slurm_%j.err            # Error file name
#SBATCH --account=pi_gobbert            # Account
#SBATCH --cluster=chip-cpu              # Cluster
#SBATCH --partition=match               # Partition
#SBATCH --qos=shared                    # Queue
#SBATCH --nodes=1                       # Number of nodes
#SBATCH --ntasks-per-node=1             # MPI processes per node
#SBATCH --time=00:05:00                 # Time limit
#SBATCH --mem=8G                        # Memory per node

module load intel/2024a
unset I_MPI_PMI_LIBRARY
export I_MPI_JOB_RESPECT_PROCESS_PLACEMENT=0
mpirun -print-rank-map ./power   8192 1.0e-12 50

