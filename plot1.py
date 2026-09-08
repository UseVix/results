#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib 
import matplotlib.ticker as ticker
import sys
from adjustText import adjust_text

# ------------------------
# LOAD CSV
# ------------------------
df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else 'compression_stats.csv')
df['method'] = df['method'].replace('Draco sequential default quantization', 'Draco Sequential')

df['time_ms'] = df['time_mean_usec'] / 1000

# Add "No compression"
no_compression = pd.DataFrame({
    'method': ['No compression'],
    'ratio_mean': [1.0],
    'time_ms': [0.0]
})
df = pd.concat([no_compression, df], ignore_index=True)
print(df[['method',  'time_p_value', 'decompress_p_value','ratio_p_value']])
# ------------------------
# AUTO-GENERATE SORT ORDER
# ------------------------
def sort_key(method):
    if method == "No compression":
        return (0, 0)
    if method.startswith("LZ4") or method.startswith("ZSTD"):
        return (1, 0)
    if method.startswith("Cloudini-ZSTD"):
        level = float(method.split()[-1].replace("p", "."))
        return (2, level)
    if method.startswith("Cloudini"):
        level = float(method.split()[-1].replace("p", "."))
        return (3, level)
    if method.startswith("Draco") and "+ ZSTD" in method:
        level = float(method.split()[1])
        return (4, level)
    if method.startswith("Draco"):
        try:
            level = float(method.split()[1])
            return (5, level)
        except:
            return (5, 0)
    if method.startswith("voxel"):
        level = float(method.split()[1])
        return (6, level)
    if method.startswith("uniform"):
        level = float(method.split()[1])
        return (7, level)
    if method.startswith("random"):
        level = float(method.split()[1])
        return (8, level)
    return (99, method)

df["sort_key"] = df["method"].apply(sort_key)
df = df.sort_values("sort_key")

# ------------------------
# COLOR MAP FOR ALL NEW CATEGORIES
# ------------------------
def get_color(method):
    if method == "No compression":
        return "#9467bd"     # purple
    if "Cloudini-ZSTD" in method:
        return "#17becf"     # strong blue
    if "Cloudini" in method:
        return "#1f77b4"     # blue
    if "+ ZSTD" in method and "Draco" in method:
        return "#ff7f0e"     # orange
    if "Draco" in method:
        return "#d62728"     # red
    if "LZ4" in method or "ZSTD only" in method:
        return "#2ca02c"     # green
    if method.startswith("voxel"):
        return "#8c564b"     # brown
    if method.startswith("uniform"):
        return "#e377c2"     # pink
    if method.startswith("random"):
        return "#7f7f7f"     # gray
    return "#000000"

colors = df["method"].apply(get_color)

# ------------------------
# PLOT 1: Compression Ratio
# ------------------------
plt.figure(figsize=(12, 7))
bars = plt.barh(df["method"], df["ratio_mean"], color=colors)
plt.gca().invert_yaxis()
plt.xlabel("Compression ratio")
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.01, bar.get_y() + bar.get_height()/2,
             f'{width:.2f}', va='center', ha='left', fontsize=12)

plt.xlim(0, df["ratio_mean"].max() * 1.1)
plt.tight_layout()
plt.savefig("method_ratio.pdf")
plt.show()

# ------------------------
# PLOT 2: Time
# ------------------------
plt.figure(figsize=(12, 7))
bars = plt.barh(df["method"], df["time_ms"], color=colors)
plt.gca().invert_yaxis()
plt.xlabel("Time [ms]")
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.5, bar.get_y() + bar.get_height()/2,
             f'{width:.1f}', va='center', ha='left', fontsize=12)

plt.xlim(0, df["time_ms"].max() * 1.1)
plt.tight_layout()
plt.savefig("method_time.pdf")
plt.show()

# ------------------------
# PLOT 3: Ratio vs Latency
# ------------------------
category_colors = {
    "Cloudini": "#1f77b4",
    "Cloudini + ZSTD": "#17becf",
    "Draco": "#d62728",
    "Draco + ZSTD": "#ff7f0e",
    "LZ4/ZSTD": "#2ca02c",
    "voxel": "#8c564b",
    "uniform": "#e377c2",
    "random": "#7f7f7f",
    "No compression": "#9467bd"
}

plt.figure(figsize=(8, 6))

def category(method):
    if method == "No compression":
        return "No compression"
    if method.startswith("Cloudini-ZSTD"):
        return "Cloudini + ZSTD"
    if method.startswith("Cloudini"):
        return "Cloudini"
    if method.startswith("Draco") and "+ ZSTD" in method:
        return "Draco + ZSTD"
    if method.startswith("Draco"):
        return "Draco"
    if method.startswith("voxel"):
        return "voxel"
    if method.startswith("uniform"):
        return "uniform"
    if method.startswith("random"):
        return "random"
    if method.startswith("LZ4") or method.startswith("ZSTD"):
        return "LZ4/ZSTD"
    return "Other"
df=df.iloc[:29]
for cat, col in category_colors.items():
    mask = df["method"].apply(category) == cat
    plt.scatter(df.loc[mask, "time_ms"],
                df.loc[mask, "ratio_mean"],
                s=80, c=col, label=cat)
texts=[]
for i, txt in enumerate(df['method']):
    texts.append(plt.text(df['time_ms'].iloc[i], df['ratio_mean'].iloc[i], txt))

# 2. Let adjustText do the magic
# arrowprops draws a faint line connecting the label to the point if it got moved
adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

plt.xlabel("Time [ms]")
plt.ylabel("Compression ratio")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig("ratio_time.pdf")
plt.show()