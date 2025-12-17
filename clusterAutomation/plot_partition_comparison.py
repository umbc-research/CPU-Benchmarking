import pandas as pd
import matplotlib.pyplot as plt
import os # <--- NEW IMPORT

# --- Config ---
TASKS_TO_PLOT = 1 
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
# ------------------------------

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
filename = f'partition_comparison_{TASKS_TO_PLOT}tasks.png'
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, filename)

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

print(f"Filtering for all NPerNode={TASKS_TO_PLOT} tests...")
df_filtered = df[
    (df['NPerNode'] == TASKS_TO_PLOT) &
    (df['Partition'].isin(['2018', '2021', '2024']))
]

if df_filtered.empty:
    print(f"No data found with {TASKS_TO_PLOT} tasks.")
else:
    if df_filtered['Time_sec'].isnull().all():
        print("Found data, but all 'Time_sec' values were invalid after parsing.")
        exit()
        
    print(f"Comparing partitions using {df_filtered['Time_sec'].notnull().sum()} valid data points...")

    plt.figure(figsize=(10, 7))
    df_filtered.boxplot(column='Time_sec', by='Partition', grid=False)
    
    plt.title(f'Performance Comparison by Partition ({TASKS_TO_PLOT} Tasks)')
    plt.suptitle('') 
    plt.xlabel('Partition')
    plt.ylabel('Time (seconds)')
    
    plt.savefig(OUTPUT_IMAGE)
    print(f"Success! Plot saved to {OUTPUT_IMAGE}")
