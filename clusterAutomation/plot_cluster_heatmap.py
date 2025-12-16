import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os

# --- CONFIG ---
TARGET_THREADS = 1 
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
# ----------------

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Data
try:
    df = pd.read_csv(CSV_FILE, skipinitialspace=True)
except FileNotFoundError:
    print(f"Error: {CSV_FILE} not found.")
    exit()
except pd.errors.EmptyDataError:
    print(f"Error: {CSV_FILE} is empty.")
    exit()

if df.empty:
    print("No data available.")
    exit()

# 2. Robust Parsing
df['Time_sec_Parsed'] = df['Time_sec'].astype(str).str.split().str[3]
df['Time_sec'] = pd.to_numeric(df['Time_sec_Parsed'], errors='coerce')
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Filter for target threads
df_filtered = df[df['NPerNode'] == TARGET_THREADS].copy()
df_filtered['Date'] = df_filtered['Timestamp'].dt.date

if df_filtered.empty:
    print(f"No data found for {TARGET_THREADS} threads.")
    exit()

# 3. Define Partition Logic
def get_partition_group(node):
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    if node.startswith('c18'): return '2018'
    return 'Other'

df_filtered['PartitionGroup'] = df_filtered['Node'].apply(get_partition_group)

# --- HELPER FUNCTION TO PLOT ---
def generate_heatmap(data, title_label, filename_label):
    if data.empty:
        print(f"  -> No data for {title_label}, skipping.")
        return

    # Pivot: Rows=Node, Cols=Date, Values=Time
    heatmap_data = data.pivot_table(index='Node', columns='Date', values='Time_sec')
    
    # Sort Index (Alphabetical sort works well here: c18 -> c21 -> c24)
    heatmap_data = heatmap_data.sort_index()
    
    # Dynamic Height: Make the plot taller if there are more nodes
    # Minimum 6 inches, add 0.3 inch per node
    fig_height = max(6, len(heatmap_data) * 0.3)
    
    plt.figure(figsize=(12, fig_height))
    
    # Plot Heatmap (Red=Slow, Green=Fast)
    plt.imshow(heatmap_data, cmap='RdYlGn_r', aspect='auto') 

    # Colorbar
    cbar = plt.colorbar()
    cbar.set_label('Time (s)')

    # Axis Labels
    plt.yticks(range(len(heatmap_data.index)), heatmap_data.index, fontsize=9)
    plt.xticks(range(len(heatmap_data.columns)), heatmap_data.columns, rotation=45, ha='right')
    
    plt.title(f'Performance Heatmap: {title_label} ({TARGET_THREADS} Threads)', fontsize=14)
    plt.tight_layout()
    
    # Save
    filename = f'heatmap_{filename_label}.png'
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    plt.close() 
    print(f"  -> Saved to {save_path}")

# 4. Main Loop

# A. Generate Individual Partition Maps
groups = ['2024', '2021', '2018']
for group_name in groups:
    print(f"Generating heatmap for {group_name}...")
    df_group = df_filtered[df_filtered['PartitionGroup'] == group_name]
    generate_heatmap(df_group, group_name, group_name)

# B. Generate Combined Map
print("Generating Combined heatmap...")
generate_heatmap(df_filtered, "All Partitions Combined", "Combined")

print("Done.")
