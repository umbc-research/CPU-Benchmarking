#!/bin/bash
source ~/.bashrc

# --- Make script "cron-safe" ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"
# --- END NEW BLOCK ---

CWD=$(pwd)
echo "Starting study in: ${CWD}"

# --- Get full command paths for cron ---
SINFO_CMD="/cm/shared/apps/slurm/current/bin/sinfo" # <-- UPDATE THIS PATH if needed (check with `which sinfo`)
if [ ! -f "${SINFO_CMD}" ]; then
    echo "Error: sinfo command not found at ${SINFO_CMD}."
    exit 1
fi
SQUEUE_CMD="/cm/shared/apps/slurm/current/bin/squeue" # <-- UPDATE THIS PATH if needed (check with `which squeue`)
if [ ! -f "${SQUEUE_CMD}" ]; then
    echo "Error: squeue command not found at ${SQUEUE_CMD}."
    exit 1
fi
# --- End command paths ---

NODE_LIST=$(sinfo -M chip-cpu -o "%n" -p 2018,test,2021,2024 | tail -n +3)

# For each problem size N...
for N in 65536
do
    STUDY_NAME=$(printf 'N%07d' ${N})
    for NPERNODE in 1 2 4 8 16 32 64
    do
        for NODE in ${NODE_LIST}
        do
            NODES=1 
            # Directory uses padded numbers (e.g., n01ppn01)
            DIR_NAME=$(printf '%s/n%02dppn%02d_%s' ${STUDY_NAME} ${NODES} ${NPERNODE} ${NODE})

            if [ ! -d "${DIR_NAME}" ]; then
                continue
            fi
            
            # --- THE FIX IS HERE ---
            # We explicitly format the job name to remove any ambiguity
            # In create-study.bash we used: JOB_NAME="power-${NPERNODE}-${NODENUMBER}"
            # So if NPERNODE is 1, it is "power-1-c24-01", NOT "power-01-c24-01"
            # We simply use the raw variable here to match that.
            JOB_NAME="power-${NPERNODE}-${NODE}"
            
            # CHECK:
            # Run squeue looking for this EXACT name.
            # We redirect output to a variable.
            JOB_STATE=$($SQUEUE_CMD -M chip-cpu -h -o "%t" -n "${JOB_NAME}" -u "$USER" | grep -v "CLUSTER")

            if [ -z "${JOB_STATE}" ]; then
                echo "Submitting job in: ${DIR_NAME}"
                cd "${DIR_NAME}"
                SUBMIT_OUTPUT=$(sbatch run.slurm 2>&1)
                echo "  -> NEW: ${SUBMIT_OUTPUT}"
                cd "${CWD}"
            else
                # This is the message you were missing
                echo "SKIP (Job '${JOB_NAME}' found in state: ${JOB_STATE})"
            fi
            
        done
    done
done

echo "All tests attempted."
