import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os # <--- NEW IMPORT

# --- Config ---
NODE_TO_PLOT = 'c24-01'
TASKS_TO_PLOT = 64
CSV_FILE = 'performance_results.csv'
OUTPUT_DIR = 'plots' # <--- NEW CONFIG
# ------------------------------

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
filename = f'performance_{NODE_TO_PLOT}_{TASKS_TO_PLOT}tasks.png'
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
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

print(f"Filtering for Node={NODE_TO_PLOT}, NPerNode={TASKS_TO_PLOT}...")
df_filtered = df[
    (df['Node'] == NODE_TO_PLOT) &
    (df['NPerNode'] == TASKS_TO_PLOT)
]

if df_filtered.empty:
    print(f"No data found for {NODE_TO_PLOT} with {TASKS_TO_PLOT} tasks.")
else:
    if df_filtered['Time_sec'].isnull().all():
        print("Found data, but all 'Time_sec' values were invalid after parsing.")
        exit()
        
    plt.figure(figsize=(12, 6))
    plt.plot(df_filtered['Timestamp'], df_filtered['Time_sec'], 
             marker='o', linestyle='-')
    
    plt.title(f'Performance of {NODE_TO_PLOT} ({TASKS_TO_PLOT} Tasks) Over Time')
    plt.xlabel('Date')
    plt.ylabel('Time (seconds)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()
    
    plt.savefig(OUTPUT_IMAGE)
    print(f"Success! Plot saved to {OUTPUT_IMAGE}")
