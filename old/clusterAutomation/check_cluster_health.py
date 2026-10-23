import pandas as pd
import datetime
import numpy as np

# --- CONFIG ---
CSV_FILE = 'performance_results.csv'
Z_SCORE_THRESHOLD = 2.0 
HISTORY_DAYS = 35
# ----------------

# 1. Load Data
try:
    df = pd.read_csv(CSV_FILE, skipinitialspace=True)
except:
    print("No data found.")
    exit()

if df.empty:
    exit()

# Robust Parsing
df['Time_sec_Parsed'] = df['Time_sec'].astype(str).str.split().str[3]
df['Time_sec'] = pd.to_numeric(df['Time_sec_Parsed'], errors='coerce')

# --- TIMEZONE FIX IS HERE ---
# 1. utc=True: Standardizes everything to UTC
# 2. .dt.tz_localize(None): Removes the timezone "sticker", making it comparable to simple dates
df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True).dt.tz_localize(None)
# ----------------------------

# 2. Assign Partitions
def get_partition_name(node):
    # Handle Test Partition
    if node.startswith('c18'): return '2018'
    if node.startswith('c24'): return '2024'
    if node.startswith('c21'): return '2021'
    return 'Other'

df['Partition'] = df['Node'].apply(get_partition_name)

# 3. Calculate Baseline Stats (Last 3 Weeks)
cutoff_date = pd.Timestamp.now().normalize() - pd.Timedelta(days=HISTORY_DAYS)
df_history = df[df['Timestamp'] >= cutoff_date].copy()

if df_history.empty:
    print("No data found in the last 3 weeks.")
    exit()

# Calculate Mean and Std Dev for every (Partition, NPerNode) combination based on history
stats = df_history.groupby(['Partition', 'NPerNode'])['Time_sec'].agg(['mean', 'std']).reset_index()

# 4. Analyze TODAY'S Performance
today = pd.Timestamp.now().normalize()

# Filter for today
df_today = df[df['Timestamp'].dt.normalize() == today].copy()

print(f"\n--- CLUSTER HEALTH REPORT: {today.date()} ---")
print(f"(Baseline calculated using data from {df_history['Timestamp'].min().date()} to Present)\n")

if df_today.empty:
    print(f"No data found for date: {today.date()}")
    print("Did the tests run today?")
    exit()

issues_found = False

# Iterate through today's results and compare to baseline
for index, row in df_today.iterrows():
    partition = row['Partition']
    threads = row['NPerNode']
    time_today = row['Time_sec']
    node = row['Node']

    # Find the baseline stats for this node's group
    group_stats = stats[(stats['Partition'] == partition) & (stats['NPerNode'] == threads)]
    
    if group_stats.empty:
        continue 
        
    mean_hist = group_stats['mean'].values[0]
    std_hist = group_stats['std'].values[0]

    # If we don't have enough history to have a std dev, we can't judge outliers
    if pd.isna(std_hist) or std_hist == 0:
        continue

    # Calculate Z-Score
    z_score = (time_today - mean_hist) / std_hist
    
    # Check if it exceeds threshold (Positive Z-score means SLOWER time)
    if z_score > Z_SCORE_THRESHOLD:
        issues_found = True
        print(f"🔴 SLOW NODE: {node} ({partition}, {threads} threads)")
        print(f"   Time: {time_today:.2f}s")
        print(f"   Baseline ({HISTORY_DAYS}d): {mean_hist:.2f}s ± {std_hist:.2f}s")
        print(f"   Deviation: +{z_score:.1f}x standard deviations")
        print("-" * 30)

if not issues_found:
    print("✅ All nodes performed within normal parameters today.")
