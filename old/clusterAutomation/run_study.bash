#!/bin/bash

nodename=$(hostname -s)
if [ ! "$nodename" = 'chip-login1' ]; then
  exit 0
fi

source ~/.bashrc

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"

CWD=$(pwd)
echo "Starting study in: ${CWD}"

# --- Get full command paths for cron ---
SINFO_CMD="/cm/shared/apps/slurm/current/bin/sinfo"
if [ ! -f "${SINFO_CMD}" ]; then
    echo "Error: sinfo command not found at ${SINFO_CMD}."
    exit 1
fi

SQUEUE_CMD="/cm/shared/apps/slurm/current/bin/squeue"
if [ ! -f "${SQUEUE_CMD}" ]; then
    echo "Error: squeue command not found at ${SQUEUE_CMD}."
    exit 1
fi

SBATCH_CMD="/cm/shared/apps/slurm/current/bin/sbatch"
if [ ! -f "${SBATCH_CMD}" ]; then
    echo "Error: sbatch command not found at ${SBATCH_CMD}."
    exit 1
fi
# --- End command paths ---

# NOTE: Updated to use the variable $SINFO_CMD instead of just 'sinfo'
NODE_LIST=$($SINFO_CMD -M chip-cpu -o "%n" -p 2018,2021,2024 | tail -n +3)

# For each problem size N...
for N in 131328
do
    STUDY_NAME=$(printf 'N%07d' ${N})
    for NPERNODE in 12 24 36
    do
        for NODE in ${NODE_LIST}
        do
            NODES=1
            # Directory uses padded numbers (e.g., n01ppn01)
            DIR_NAME=$(printf '%s/n%02dppn%02d_%s' ${STUDY_NAME} ${NODES} ${NPERNODE} ${NODE})

            if [ ! -d "${DIR_NAME}" ]; then
                continue
            fi

            # We explicitly format the job name to remove any ambiguity
            JOB_NAME="power-${NPERNODE}-${NODE}"

            # Run squeue looking for this EXACT name.
            JOB_STATE=$($SQUEUE_CMD -M chip-cpu -h -o "%t" -n "${JOB_NAME}" -u "$USER" | grep -v "CLUSTER")

            if [ -z "${JOB_STATE}" ]; then
                echo "Submitting job in: ${DIR_NAME}"
                cd "${DIR_NAME}"

                # NOTE: Updated to use $SBATCH_CMD
                SUBMIT_OUTPUT=$($SBATCH_CMD run.slurm 2>&1)

                echo "  -> NEW: ${SUBMIT_OUTPUT}"
   
                cd "${CWD}"
            else
                echo "SKIP (Job '${JOB_NAME}' found in state: ${JOB_STATE})"
            fi

        done
    done
done

echo "All tests attempted."

# Graph Generation:
# Check if there are any .png files in the plots directory modified in the last 30 days
if [ -d "${CWD}/plots" ]; then
    RECENT_PLOTS=$(find "${CWD}/plots" -maxdepth 1 -type f -name "*.png" -mtime -30 -print -quit)
else
    # If the directory doesn't exist, we treat it as needing new plots
    RECENT_PLOTS=""
fi

# If RECENT_PLOTS is empty, it means no graphs have been generated in the last 30 days
if [ -z "${RECENT_PLOTS}" ]; then
    echo "Graphs are a month old (or don't exist). Submitting graph generation..."
    $SBATCH_CMD generate_graphs.slurm
else
    echo "Recent graphs found in ./plots (less than 30 days old). Skipping graph generation."
fi
