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
TARGET_THREADS_LIST = [12, 24, 36]  # Updated to loop through multiple thread counts
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots'
HISTORY_DAYS = 35
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

# 2. Define Partitions
def get_partition_group(node):
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    if node.startswith('c18'): return '2018'
    return 'Other'

df['PartitionGroup'] = df['Node'].apply(get_partition_group)

# 3. Set Time Windows
today = pd.Timestamp.now().normalize()
date_str = today.strftime('%Y-%m-%d') # Generate the date string for filenames

cutoff_date = today - pd.Timedelta(days=HISTORY_DAYS)

# 4. Generate Plot for Each Group AND Thread Count
groups = ['2024', '2021', '2018']

for group in groups:
    for threads in TARGET_THREADS_LIST:
        print(f"Analyzing distribution for {group} at {threads} threads...")

        # Get Data filtered by both group and thread count
        df_filtered = df[(df['PartitionGroup'] == group) & (df['NPerNode'] == threads)]
        if df_filtered.empty: 
            print(f"  -> No data for {group} at {threads} threads. Skipping.")
            continue

        # History Data (Baseline)
        df_hist = df_filtered[(df_filtered['Timestamp'] >= cutoff_date) & (df_filtered['Timestamp'] < today)]

        if df_hist.empty:
            print(f"  -> Not enough history for {group} ({threads}t). Using all data.")
            df_hist = df_filtered

        # Today's Data (Targets)
        df_today = df_filtered[df_filtered['Timestamp'].dt.normalize() == today]

        # Stats
        mu = df_hist['Time_sec'].mean()
        sigma = df_hist['Time_sec'].std()

        if pd.isna(sigma) or sigma == 0:
            print(f"  -> Variance is zero or NaN for {group} ({threads}t), skipping plot.")
            continue

        # --- DYNAMIC X-AXIS FIX ---
        # Extreme historical outliers push everything left. We cap the visual range to center the curve.
        x_min = max(0, mu - 4 * sigma)
        today_max = df_today['Time_sec'].max() if not df_today.empty else mu
        
        # Ensure the plot is wide enough to show today's max value OR 4 standard deviations from the mean
        x_max = max(mu + 4 * sigma, today_max * 1.05)

        # --- PLOTTING ---
        plt.figure(figsize=(12, 7))

        # A. The Histogram
        # Using the range parameter so bins are only calculated within our visual window
        n, bins, patches = plt.hist(df_hist['Time_sec'], bins=25, range=(x_min, x_max), density=True,
                                    alpha=0.3, color='gray', edgecolor='none',
                                    label=f'3-Week Baseline (N={len(df_hist)})')

        max_hist_height = max(n) if len(n) > 0 else 0.1

        # B. The Normal Curve
        x = np.linspace(x_min, x_max, 200)
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
                plt.scatter(today_outliers['Time_sec'], [dot_y] * len(today_outliers),
                            color='red', marker='x', s=100, linewidth=2,
                            label=f"Today: Outliers (>{Z_SCORE_THRESHOLD}$\\sigma$)", zorder=4)

                for _, row in today_outliers.iterrows():
                    val = row['Time_sec']
                    node = row['Node']
                    z_score = (val - mu) / sigma

                    label_text = f"{node}\n(+{z_score:.1f}$\\sigma$)"

                    t = plt.text(val, dot_y + (max_hist_height * 0.02), label_text,
                                 ha='center', va='bottom', color='darkred', fontsize=9)
                    texts.append(t)

        # Formatting
        plt.title(f'Performance Check: {group}\nTarget Threads: {threads}', fontsize=14, fontweight='bold')
        plt.xlabel('Execution Time (seconds)')
        plt.ylabel('Probability Density')
        plt.xlim(x_min, x_max) # Lock the axes to our calculated visual window
        plt.grid(axis='y', alpha=0.2)
        plt.legend(loc='upper right', frameon=True)

        # Ensure enough headroom for labels
        plt.ylim(0, max(max(p), max_hist_height) * 1.3)

        if texts:
            adjust_text(texts,
                        arrowprops=dict(arrowstyle='-', color='red', lw=0.5),
                        time_lim=1
                       )

        # Save with the requested dynamic filename
        filename = f'distribution_{group}_{threads}threads_{date_str}.png'
        save_path = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close()
        print(f"  -> Saved {filename}")

print("Done.")
