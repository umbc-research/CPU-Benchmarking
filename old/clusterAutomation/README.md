Cluster Performance Benchmarking

This directory contains the automated benchmarking suite used to monitor the health and performance of the cluster nodes over time.

🚀 Quick Start & Environment

Python Environment
To run any of the .py plotting or analysis scripts, you must first activate the specific Conda environment:

conda activate BenchmarkingPythonEnvironment



Automation (Cron)
The daily automation is managed via the root crontab.

Node: The cron job is configured as root chip-login1. It is also in the image at: /cm/images/login-q1-26/etc/cron.d/benchmarking

You can SSH to that node to edit the crontab (crontab -e) if schedule changes are needed.

0 3 * * * su - elliotg2 -c "/bin/bash /umbc/rs/pi_doit/users/elliotg2/benchmarking/clusterAutomation/run_study.bash > /umbc/rs/pi_doit/users/elliotg2/benchmarking/clusterAutomation/cron_log.txt 2>&1"

In the image, the line is slightly different:

0 3 * * * elliotg2 /bin/bash /umbc/rs/pi_doit/users/elliotg2/benchmarking/clusterAutomation/run_study.bash > /umbc/rs/pi_doit/users/elliotg2/benchmarking/clusterAutomation/cron_log.txt 2>&1

📂 File Descriptions

1. Core Automation (Bash)

    create_study.bash: Initializes directory structures and generates per-node SLURM scripts.

    run_study.bash: Daily automation script; submits jobs via Cron while preventing duplicate submissions. Graphs are generated monthly.

    power: The binary executable for the benchmark tests.

2. Analysis & Reporting (Python)

    check_cluster_health.py: Identifies statistically slow nodes (>2 SD) compared to a 3-week baseline.

    plot_cluster_heatmap.py: Visualizes partition health with color-coded speed maps.

    plot_distribution_check.py: Uses histograms and bell curves to identify cluster-wide performance outliers.

    plot_partition_comparison.py: Uses box plots to compare performance across different hardware generations.

    plot_node_performance.py: Generates a detailed performance history for a specific machine.

3. Data & Storage

    performance_results.csv: The central database for benchmark metrics (Time, Node, Memory).

    performance_results.csv.lock: Prevents data corruption during simultaneous writes.

    cron_log.txt: Records daily execution status and errors.

    N0065536/: Storage for current job folders and active SLURM scripts.

    plots/: Repository for all generated PNG charts and graphs.
