import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import os
# --- NEW IMPORT ---
try:
    from adjustText import adjust_text
except ImportError:
    print("ERROR: Please install adjustText: 'pip install adjustText'")
    exit()
# ------------------

# --- CONFIG ---
TARGET_THREADS = 1
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
HISTORY_DAYS = 21
# Changed Z-score as requested
Z_SCORE_THRESHOLD = 3.0
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
        try:
            if 43 <= int(node.split('-')[1]) <= 50: return '2018_Mixed'
        except: pass
        return '2018_Mixed'
    return 'Other'

df['PartitionGroup'] = df['Node'].apply(get_partition_group)

# 3. Set Time Windows
today = pd.Timestamp.now().normalize()
# today = df['Timestamp'].max().normalize() # Uncomment for testing on old data

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
    plt.figure(figsize=(12, 7))
    
    # A. The Histogram
    n, bins, patches = plt.hist(df_hist['Time_sec'], bins=20, density=True,
                                alpha=0.3, color='gray', edgecolor='none', 
                                label=f'3-Week Baseline (N={len(df_hist)})')
    
    max_hist_height = max(n) if len(n) > 0 else 0.1

    # B. The Normal Curve
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 200)
    p = stats.norm.pdf(x, mu, sigma)
    
    plt.plot(x, p, 'k--', linewidth=1.5, alpha=0.7, 
             label=f'Normal Curve ($\\mu$={mu:.2f}, $\\sigma$={sigma:.2f})')

    # C. Today's Points
    texts = [] # Initialize list to collect label objects

    if not df_today.empty:
        outlier_limit = mu + (Z_SCORE_THRESHOLD * sigma)
        
        today_outliers = df_today[df_today['Time_sec'] > outlier_limit]
        today_normal = df_today[df_today['Time_sec'] <= outlier_limit]
        
        # Define Y-height for dots slightly higher than before for better label placement
        dot_y = max_hist_height * 0.08 
        
        # 1. Plot Normal Nodes
        if not today_normal.empty:
            plt.scatter(today_normal['Time_sec'], [dot_y] * len(today_normal), 
                        color='green', s=50, alpha=0.5, edgecolors='none', 
                        label="Today: Normal Nodes", zorder=3)

        # 2. Plot Outliers
        if not today_outliers.empty:
            # Plot the Red X markers
            plt.scatter(today_outliers['Time_sec'], [dot_y] * len(today_outliers), 
                        color='red', marker='x', s=100, linewidth=2, 
                        label=f"Today: Outliers (>{Z_SCORE_THRESHOLD}$\\sigma$)", zorder=4)

            # Collect labels for adjustText
            for _, row in today_outliers.iterrows():
                val = row['Time_sec']
                node = row['Node']
                z_score = (val - mu) / sigma
                
                label_text = f"{node}\n(+{z_score:.1f}$\\sigma$)"
                
                # Place initial text object slightly above the dot
                # We use plain plt.text here, adjust_text will handle the arrows later
                t = plt.text(val, dot_y + (max_hist_height * 0.02), label_text,
                             ha='center', va='bottom', color='darkred', fontsize=9)
                texts.append(t)

    # Formatting
    plt.title(f'Performance Check: {group}\nTarget Threads: {TARGET_THREADS}', fontsize=14, fontweight='bold')
    plt.xlabel('Execution Time (seconds)')
    plt.ylabel('Probability Density')
    plt.grid(axis='y', alpha=0.2)
    plt.legend(loc='upper right', frameon=True)
    
    # Ensure enough headroom for labels
    plt.ylim(0, max(max(p), max_hist_height) * 1.3)

    # --- THE MAGIC STEP: Adjust Text ---
    # This moves the collected text objects apart and draws lines to their origins
    if texts:
        # time_lim=1 ensures it doesn't spend forever trying to optimize if it's impossible
        adjust_text(texts, 
                    arrowprops=dict(arrowstyle='-', color='red', lw=0.5),
                    time_lim=1
                   )

    filename = f'distribution_{group}.png'
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  -> Saved {filename}")

print("Done.")
