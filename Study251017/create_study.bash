#!/bin/bash

# --- Get CWD for results file path ---
CWD=$(pwd)

# --- Get Node List ---
NODE_LIST=$(sinfo -M chip-cpu -o "%n" -p 2018,test,2021,2024 | tail -n +3)

# Define the central results file
RESULTS_FILE="${CWD}/performance_results.csv"

# --- Initialize CSV file with new headers ---
if [ ! -f "${RESULTS_FILE}" ]; then
    echo "Creating new results file: ${RESULTS_FILE}"
    echo "Timestamp,Node,N,NPerNode,Time_sec,Memory_kB" > ${RESULTS_FILE}
fi

# This function writes a SLURM script.
function write_script
{
    local NODENUMBER=$1
    local NODES=1
    local PARTITION_NAME=""
    local QOS_NAME=""

    # --- Set Partition and QOS Based on Node Name ---
    case "${NODENUMBER}" in
        # NEW: Handle the special 'test' partition nodes (c18-43 to c18-50)
        c18-4[3-9]|c18-50)
            PARTITION_NAME="test"
            QOS_NAME="support"
            ;;
        c24*)
            PARTITION_NAME="2024"
            QOS_NAME="shared"
            ;;
        c21*)
            PARTITION_NAME="2021"
            QOS_NAME="normal"
            ;;
        c18*)
            PARTITION_NAME="2018"
            QOS_NAME="normal"
            ;;
        *)
            echo "Warning: Unknown prefix for node ${NODENUMBER}. Defaulting." >&2
            PARTITION_NAME="match"
            QOS_NAME="shared"
            ;;
    esac

    STUDY_NAME=$(printf 'N%07d' ${N})
    DIR_NAME=$(printf '%s/n%02dppn%02d_%s' ${STUDY_NAME} ${NODES} ${NPERNODE} ${NODENUMBER})

    echo "Creating test directory: $DIR_NAME (Partition: $PARTITION_NAME)"
    mkdir -p $DIR_NAME

    local JOB_NAME="power-${NPERNODE}-${NODENUMBER}"

    # --- Start of SLURM script template ---
    cat << _EOF_ > ${DIR_NAME}/run.slurm
#!/bin/bash
#SBATCH --job-name=${JOB_NAME}
#SBATCH --output=slurm.out  
#SBATCH --error=slurm.err
#SBATCH --cluster=chip-cpu
#SBATCH --account=pi_doit
#SBATCH --partition=${PARTITION_NAME}
#SBATCH --qos=${QOS_NAME}
#SBATCH --nodelist=${NODENUMBER}
#SBATCH --ntasks-per-node=${NPERNODE}
#SBATCH --time=01:55:00
#SBATCH --mem=100G

module load intel/2024a
unset I_MPI_PMI_LIBRARY
export I_MPI_JOB_RESPECT_PROCESS_PLACEMENT=0

mpirun ../../power ${N} 1.0e-12 50

# --- DATA COLLECTION ---
if [ -s "diag_time.dat" ] && [ -s "memory.log" ]; then
    TIME_VALUE=\$(awk '{print $4}' diag_time.dat)
    MEM_VALUE=\$(awk '/Overall usage/ {print $3}' memory.log)
    TIMESTAMP=\$(date --iso-8601=seconds)
    CSV_LINE="\${TIMESTAMP},${NODENUMBER},${N},${NPERNODE},\${TIME_VALUE},\${MEM_VALUE}"
    flock ${RESULTS_FILE}.lock -c "echo \"\${CSV_LINE}\" >> ${RESULTS_FILE}"
else
    echo "Error: Output files (diag_time.dat, memory.log) not found or are empty." >&2
fi
_EOF_
}

# --- Main loops ---
for N in 65536
do
    for NPERNODE in 1 2 4 8 16 32 64
    do
        for NODE in ${NODE_LIST}
        do
            write_script ${NODE}
        done
    done
done
