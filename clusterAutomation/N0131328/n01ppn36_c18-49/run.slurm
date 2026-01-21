#!/bin/bash
#SBATCH --job-name=power-36-c18-49
#SBATCH --output=slurm.out  
#SBATCH --error=slurm.err
#SBATCH --cluster=chip-cpu
#SBATCH --account=pi_doit
#SBATCH --partition=support
#SBATCH --qos=support
#SBATCH --nodelist=c18-49
#SBATCH --ntasks-per-node=36
#SBATCH --time=08:00:00
#SBATCH --mem=150G

module load intel/2024a
unset I_MPI_PMI_LIBRARY
export I_MPI_JOB_RESPECT_PROCESS_PLACEMENT=0

mpirun ../../power 131328 1.0e-12 50

# --- DATA COLLECTION ---
if [ -s "diag_time.dat" ] && [ -s "memory.log" ]; then
    TIME_VALUE=$(awk '{print }' diag_time.dat)
    MEM_VALUE=$(awk '/Overall usage/ {print }' memory.log)
    TIMESTAMP=$(date --iso-8601=seconds)
    CSV_LINE="${TIMESTAMP},c18-49,131328,36,${TIME_VALUE},${MEM_VALUE}"
    flock /home/elliotg2/doit_user/benchmarking/clusterAutomation/performance_results.csv.lock -c "echo \"${CSV_LINE}\" >> /home/elliotg2/doit_user/benchmarking/clusterAutomation/performance_results.csv"
else
    echo "Error: Output files (diag_time.dat, memory.log) not found or are empty." >&2
fi
