import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import os

# --- CONFIG ---
TARGET_THREADS = 1 
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
HISTORY_DAYS = 21
Z_SCORE_THRESHOLD = 2.0
# ----------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load and Parse
try:
    df = pd.read_csv(CSV_FILE, skipinitialspace=True)
except:
    print("No data found.")
    exit()

if df.empty: exit()

# Robust Parsing
df['Time_sec_Parsed'] = df['Time_sec'].astype(str).str.split().str[3]
df['Time_sec'] = pd.to_numeric(df['Time_sec_Parsed'], errors='coerce')
# Timezone fix (UTC -> Naive)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True).dt.tz_localize(None)

# Filter for target threads
df = df[df['NPerNode'] == TARGET_THREADS].copy()

# 2. Define Partitions
def get_partition_group(node):
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    if node.startswith('c18'): 
        # Check for Test partition
        try:
            if 43 <= int(node.split('-')[1]) <= 50: return '2018_Mixed'
        except: pass
        return '2018_Mixed'
    return 'Other'

df['PartitionGroup'] = df['Node'].apply(get_partition_group)

# 3. Set Time Windows
today = pd.Timestamp.now().normalize()
# Uncomment to test on old data:
# today = df['Timestamp'].max().normalize()

cutoff_date = today - pd.Timedelta(days=HISTORY_DAYS)

# 4. Generate Plot for Each Group
groups = ['2024', '2021', '2018_Mixed']

for group in groups:
    print(f"Analyzing distribution for {group}...")
    
    # Get Data
    df_group = df[df['PartitionGroup'] == group]
    if df_group.empty: continue
    
    # History Data (Baseline)
    df_hist = df_group[(df_group['Timestamp'] >= cutoff_date) & (df_group['Timestamp'] < today)]
    
    # Fallback if no history exists (e.g. first run)
    if df_hist.empty:
        print(f"  -> Not enough history for {group}. Using all data.")
        df_hist = df_group
        
    # Today's Data (Targets)
    df_today = df_group[df_group['Timestamp'].dt.normalize() == today]
    
    # Stats
    mu = df_hist['Time_sec'].mean()
    sigma = df_hist['Time_sec'].std()
    
    if pd.isna(sigma) or sigma == 0:
        print(f"  -> Variance is zero or NaN for {group}, skipping plot.")
        continue

    # --- PLOTTING ---
    plt.figure(figsize=(10, 6))
    
    # A. The Histogram (The Reality)
    n, bins, patches = plt.hist(df_hist['Time_sec'], bins=15, density=True, 
                                alpha=0.4, color='gray', label=f'3-Week Baseline (N={len(df_hist)})')
    
    # B. The Normal Curve (The Theory)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mu, sigma)
    
    # Fixed SyntaxWarning here by using double backslashes
    plt.plot(x, p, 'r--', linewidth=2, label=f'Normal Curve ($\\mu$={mu:.2f}, $\\sigma$={sigma:.2f})')
    
    # C. Today's Points
    if not df_today.empty:
        outlier_threshold = mu + (Z_SCORE_THRESHOLD * sigma)
        
        for _, row in df_today.iterrows():
            val = row['Time_sec']
            node = row['Node']
            
            if val > outlier_threshold:
                # OUTLIER (Red Line + Text)
                plt.axvline(val, color='red', linestyle='-', linewidth=2, alpha=0.8)
                y_pos = stats.norm.pdf(val, mu, sigma)
                # Fixed SyntaxWarning here too
                plt.text(val, y_pos, f" {node}\n (+{(val-mu)/sigma:.1f}$\\sigma$)", 
                         color='red', fontsize=9, fontweight='bold', verticalalignment='bottom')
            else:
                # NORMAL (Green Line, faint)
                plt.axvline(val, color='green', linestyle='-', linewidth=1, alpha=0.3)

        plt.axvline(-100, color='green', alpha=0.5, label="Today's Normal Nodes")
        plt.axvline(-100, color='red', alpha=0.8, label="Today's Outliers")

    # Formatting
    plt.title(f'Performance Distribution: {group} ({TARGET_THREADS} Threads)\n', fontsize=14)
    plt.xlabel('Execution Time (seconds)')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.xlim(xmin, xmax) 
    
    filename = f'distribution_{group}.png'
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    plt.close()
    print(f"  -> Saved {filename}")

print("Done.")
