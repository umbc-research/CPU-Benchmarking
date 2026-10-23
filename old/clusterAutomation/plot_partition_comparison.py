import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# --- Config ---
TASKS_LIST = [12, 24, 36]
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
# ------------------------------

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d')

print(f"Loading data from {CSV_FILE}...")
try:
    df = pd.read_csv(CSV_FILE, skipinitialspace=True)
except FileNotFoundError:
    print(f"Error: {CSV_FILE} not found.")
    exit()
except pd.errors.EmptyDataError:
     print(f"Error: {CSV_FILE} is empty.")
     exit()

if df.empty:
    print(f"Error: {CSV_FILE} contains a header but no data.")
    exit()

# --- Parsing Logic ---
df['Time_sec_Parsed'] = df['Time_sec'].astype(str).str.split().str[3]
df['Time_sec'] = pd.to_numeric(df['Time_sec_Parsed'], errors='coerce')

# --- Accurate Partition Logic ---
def get_partition_name(node):
    if node.startswith('c18'): return '2018'
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    return 'Other'

df['Partition'] = df['Node'].apply(get_partition_name)

# Loop through each thread count
for tasks in TASKS_LIST:
    print(f"\nFiltering for all NPerNode={tasks} tests...")
    df_filtered = df[
        (df['NPerNode'] == tasks) &
        (df['Partition'].isin(['2018', '2021', '2024']))
    ]

    if df_filtered.empty:
        print(f"No data found with {tasks} tasks. Skipping...")
        continue

    if df_filtered['Time_sec'].isnull().all():
        print(f"Found data for {tasks} tasks, but all 'Time_sec' values were invalid after parsing. Skipping...")
        continue

    print(f"Comparing partitions using {df_filtered['Time_sec'].notnull().sum()} valid data points...")

    plt.figure(figsize=(10, 7))
    df_filtered.boxplot(column='Time_sec', by='Partition', grid=False)

    plt.title(f'Performance Comparison by Partition ({tasks} Tasks)')
    plt.suptitle('')
    plt.xlabel('Partition')
    plt.ylabel('Time (seconds)')

    # Format filename with the requested structure
    filename = f'partition_comparison_{tasks}threads_{current_date}.png'
    OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, filename)
    
    plt.savefig(OUTPUT_IMAGE)
    plt.close() # Close figure to avoid plotting over the previous chart
    print(f"Success! Plot saved to {OUTPUT_IMAGE}")
