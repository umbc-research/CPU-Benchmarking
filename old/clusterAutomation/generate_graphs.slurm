#!/bin/bash
#SBATCH --job-name=gen_graphs
#SBATCH --output=gen_graphs.out
#SBATCH --error=gen_graphs.err
#SBATCH --cluster=chip-cpu
#SBATCH --account=pi_doit
#SBATCH --partition=support
#SBATCH --qos=support
#SBATCH --ntasks=1           # Just 1 task, no parallelization needed
#SBATCH --cpus-per-task=1    # 1 CPU core
#SBATCH --time=00:10:00      # 10 minutes is plenty for plotting
#SBATCH --mem=4G             # 4GB of RAM is more than enough for Pandas

# Navigate to the directory where you submit the script (optional, but good practice)
cd $SLURM_SUBMIT_DIR

# Run the Python script using the absolute path to your Conda environment's Python
/umbc/rs/pi_gobbert/users/elliotg2/conda_envs/BenchmarkingPythonEnvironment/bin/python plot_cluster_heatmap.py

/umbc/rs/pi_gobbert/users/elliotg2/conda_envs/BenchmarkingPythonEnvironment/bin/python plot_distribution_check.py

/umbc/rs/pi_gobbert/users/elliotg2/conda_envs/BenchmarkingPythonEnvironment/bin/python plot_partition_comparison.py
