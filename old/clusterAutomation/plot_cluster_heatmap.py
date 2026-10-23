import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import datetime

# --- CONFIG ---
# Changed to a list to generate plots for multiple thread counts
TARGET_THREADS_LIST = [12, 24, 36] 
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
# ----------------

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get the current date to append to filenames
generation_date = datetime.datetime.now().strftime("%Y-%m-%d")

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
df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
df['Date'] = df['Timestamp'].dt.date

# 3. Define Partition Logic
def get_partition_group(node):
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    if node.startswith('c18'): return '2018'
    return 'Other'

# Apply partition group to the whole dataframe first
df['PartitionGroup'] = df['Node'].apply(get_partition_group)


# --- HELPER FUNCTION TO PLOT ---
def generate_heatmap(data, title_label, filename_label, threads):
    if data.empty:
        print(f"  -> No data for {title_label} ({threads} Threads), skipping.")
        return

    # Pivot: Rows=Node, Cols=Date, Values=Time
    heatmap_data = data.pivot_table(index='Node', columns='Date', values='Time_sec')

    # Sort Index (Alphabetical sort works well here: c18 -> c21 -> c24)
    heatmap_data = heatmap_data.sort_index()

    # Dynamic Height: Make the plot taller if there are more nodes
    # Minimum 6 inches, add 0.3 inch per node
    fig_height = max(6, len(heatmap_data) * 0.3)

    plt.figure(figsize=(12, fig_height))

    # --- OUTLIER HANDLING ---
    # Calculate the 5th and 95th percentiles to clip extreme values
    # This prevents single extreme outliers from skewing the colormap
    flat_values = heatmap_data.values.flatten()
    vmin = np.nanpercentile(flat_values, 5)
    vmax = np.nanpercentile(flat_values, 95)

    # Pass vmin and vmax into imshow to lock the color scale bounds
    plt.imshow(heatmap_data, cmap='viridis', aspect='auto', vmin=vmin, vmax=vmax)

    # Colorbar
    cbar = plt.colorbar()
    cbar.set_label('Time (s)')

    # --- AXIS LABELS & WEEK MARKERS ---
    plt.yticks(range(len(heatmap_data.index)), heatmap_data.index, fontsize=9)
    
    # Only label every 7th column (weekly) to prevent text clumping
    x_ticks_positions = range(0, len(heatmap_data.columns), 7)
    x_ticks_labels = heatmap_data.columns[::7]
    plt.xticks(x_ticks_positions, x_ticks_labels, rotation=45, ha='right')

    plt.title(f'Performance Heatmap: {title_label} ({threads} Threads)', fontsize=14)
    plt.tight_layout()

    # Save (Include threads and generation date in the filename)
    filename = f'heatmap_{filename_label}_{threads}threads_{generation_date}.png'
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    plt.close()
    print(f"  -> Saved to {save_path}")


# 4. Main Loop over Target Threads
for target_thread in TARGET_THREADS_LIST:
    print(f"\n=== Processing {target_thread} Threads ===")
    
    # Filter for the current thread count in the loop
    df_filtered = df[df['NPerNode'] == target_thread].copy()

    if df_filtered.empty:
        print(f"No data found for {target_thread} threads, skipping.")
        continue

    # A. Generate Individual Partition Maps
    groups = ['2024', '2021', '2018']
    for group_name in groups:
        print(f"Generating heatmap for {group_name}...")
        df_group = df_filtered[df_filtered['PartitionGroup'] == group_name]
        generate_heatmap(df_group, group_name, group_name, target_thread)

    # B. Generate Combined Map
    print("Generating Combined heatmap...")
    generate_heatmap(df_filtered, "All Partitions Combined", "Combined", target_thread)

print("\nDone.")
