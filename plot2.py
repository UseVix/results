#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import re
import numpy as np
import sys

# ------------------------
# MATPLOTLIB STYLE
# ------------------------
matplotlib.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "stix",
    "axes.labelsize": 16,
    "font.size": 12,
    "legend.fontsize": 12,
    "xtick.labelsize": 12,
    "ytick.labelsize": 14
})
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

# ------------------------
# LOAD CSV
# ------------------------
df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else 'compression_stats.csv')
df['time_ms'] = df['time_mean_usec'] / 1000.0

# Add "No compression"
no_compression = pd.DataFrame({
    'method': ['No compression'],
    'ratio_mean': [1.0],
    'time_ms': [0.0]
})
df = pd.concat([no_compression, df], ignore_index=True)

# ------------------------
# Pretty names and param extraction
# ------------------------
def pretty_method(method: str):
    if method.lower() == "no compression":
        return "No compression", 0.0, "No compression"
    if method == "LZ4 only":
        return "LZ4", 0.0, "LZ4"
    if method == "ZSTD only":
        return "ZSTD", 0.0, "ZSTD"
    if "Cloudini-ZSTD" in method:
        m = re.search(r'0p\d+', method)
        v = float(m.group(0).replace("p", ".")) if m else 0.0
        return f"Cloudini ({v}) + ZSTD", v, "Cloudini + ZSTD"
    if "Cloudini-LZ4" in method:
        m = re.search(r'0p\d+', method)
        v = float(m.group(0).replace("p", ".")) if m else 0.0
        return f"Cloudini ({v}) + LZ4", v, "Cloudini + LZ4"
    if method.startswith("Cloudini"):
        m = re.search(r'0p\d+', method)
        v = float(m.group(0).replace("p", ".")) if m else 0.0
        return f"Cloudini ({v})", v, "Cloudini"
    if "Draco" in method:
        m = re.search(r'\d+', method)
        v = int(m.group(0)) if m else 0
        if "+ ZSTD" in method:
            return f"Draco ({v}) + ZSTD", v, "Draco + ZSTD"
        return f"Draco ({v})", v, "Draco"
    if "voxel" in method or "uniform" in method or "random" in method:
        m = re.search(r'\d*\.?\d+', method)
        v = float(m.group(0)) if m else 0.0
        g = method.split()[0].capitalize()
        return f"{g} ({v})", v, g
    if "g-pcc" in method.lower():
        m = re.search(r'\d*\.?\d+', method)
        v = float(m.group(0)) if m else 0.0
        return f"G-PCC ({v})", v, "G-PCC"
    return method, 0.0, method

df[['method_pretty', 'param_value', 'group']] = df['method'].apply(
    lambda x: pd.Series(pretty_method(x))
)

# ------------------------
# GROUP ORDER
# ------------------------
group_order = [
    "No compression", "LZ4", "ZSTD",
    "Cloudini", "Cloudini + LZ4", "Cloudini + ZSTD",
    "Draco", "Draco + ZSTD",
    "Voxel", "Uniform", "Random", "G-PCC"
]
group_index = {g: i for i, g in enumerate(group_order)}
df['group_idx'] = df['group'].map(group_index)
df = df.sort_values(['group_idx', 'param_value'])

# ------------------------
# COLORS
# ------------------------
color_map = {
    "No compression": "#1b9e77",
    "LZ4": "#d95f02",
    "ZSTD": "#7570b3",
    "Cloudini": "#e7298a",
    "Cloudini + LZ4": "#e7298a",
    "Cloudini + ZSTD": "#66a61e",
    "Draco": "#e6ab02",
    "Draco + ZSTD": "#a6761d",
    "Voxel": "#666666",
    "Uniform": "#1f78b4",
    "Random": "#b2df8a",
    "G-PCC": "#fb9a99"
}
df['color'] = df['group'].apply(lambda g: color_map.get(g, "#000000"))

# ------------------------
# BAR PLOT: COMPRESSION RATIO
# ------------------------
plt.figure(figsize=(12, 12))
bars = plt.barh(df['method_pretty'], df['ratio_mean'], color=df['color'])
plt.gca().invert_yaxis()
plt.xlabel("Compression ratio")
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    w = bar.get_width()
    plt.text(w + 0.01, bar.get_y() + bar.get_height()/2,
             f"{w:.2f}", va="center")

plt.xlim(0, df['ratio_mean'].max() * 1.1)
plt.tight_layout()
plt.savefig("method_ratio.pdf")
plt.show()

# ------------------------
# BAR PLOT: TIME
# ------------------------
plt.figure(figsize=(12, 12))
bars = plt.barh(df['method_pretty'], df['time_ms'], color=df['color'])
plt.gca().invert_yaxis()
plt.xlabel("Time [ms]")
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    w = bar.get_width()
    plt.text(w + 0.5, bar.get_y() + bar.get_height()/2,
             f"{w:.1f}", va="center")

plt.xlim(0, df['time_ms'].max() * 1.1)
plt.tight_layout()
plt.savefig("method_time.pdf")
plt.show()

# ------------------------
# LINE PLOTS: PARAM vs RATIO
# ------------------------
def plot_param_vs_ratio(groups, title, filename):
    plt.figure(figsize=(8, 6))
    for g in groups:
        sub = df[(df['group'] == g) & (df['param_value'] > 0)]
        if sub.empty:
            continue
        plt.plot(
            sub['param_value'],
            sub['ratio_mean'],
            marker='o',
            linewidth=2,
            label=g,
            color=color_map[g]
        )
    plt.xlabel("Parameter value")
    plt.ylabel("Compression ratio")
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()

# Cloudini
plot_param_vs_ratio(
    ["Cloudini", "Cloudini + LZ4", "Cloudini + ZSTD"],
    "Cloudini: parameter vs compression ratio",
    "cloudini_param_vs_ratio.pdf"
)

# Draco
plot_param_vs_ratio(
    ["Draco", "Draco + ZSTD"],
    "Draco: parameter vs compression ratio",
    "draco_param_vs_ratio.pdf"
)

# Others
plot_param_vs_ratio(["Voxel"], "Voxel: parameter vs compression ratio", "voxel_param_vs_ratio.pdf")
plot_param_vs_ratio(["Uniform"], "Uniform: parameter vs compression ratio", "uniform_param_vs_ratio.pdf")
plot_param_vs_ratio(["Random"], "Random: parameter vs compression ratio", "random_param_vs_ratio.pdf")
plot_param_vs_ratio(["G-PCC"], "G-PCC: parameter vs compression ratio", "gpcc_param_vs_ratio.pdf")

# ------------------------
# SUBPLOTS: PARAM vs RATIO
# ------------------------

fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharey=True)
axes = axes.flatten()

plots = [
    (["Cloudini", "Cloudini + LZ4", "Cloudini + ZSTD"], "Cloudini"),
    (["Draco", "Draco + ZSTD"], "Draco"),
    (["Voxel"], "Voxel"),
    (["Uniform"], "Uniform"),
    (["Random"], "Random"),
    (["G-PCC"], "G-PCC"),
]

from matplotlib.ticker import FuncFormatter

x_axis_config = {
    "Cloudini": {
        "xlabel": "Compression resolution [m]",
        "xscale": "log",
        "invert": False
    },
    "Cloudini + LZ4": {
        "xlabel": "Compression resolution [m]",
        "xscale": "log",
        "invert": False
    },
    "Cloudini + ZSTD": {
        "xlabel": "Compression resolution [m]",
        "xscale": "log",
        "invert": False
    },

    "Draco": {
        "xlabel": "Quantization [bit]",
        "invert": True
    },
    "Draco + ZSTD": {
        "xlabel": "Quantization [bit]",
        "invert": True
    },

    "G-PCC": {
        "xlabel": "Quantization [m]",
        "xscale": "log",
        "invert": True
    },

    "Voxel": {
        "xlabel": "Leaf size [m]"
    },

    "Random": {
        "xlabel": "Retained fraction [%]",
        "invert": True,
        "formatter": FuncFormatter(lambda x, _: f"{int(x * 100)}%")
    },

    "Uniform": {
        "xlabel": "Leaf size [m]"
    }
}

for ax, (groups, title) in zip(axes, plots):
    for g in groups:
        sub = df[(df['group'] == g) & (df['param_value'] > 0)]
        if sub.empty:
            continue

        ax.plot(
            sub['param_value'],
            sub['ratio_mean'],
            marker='o',
            linewidth=2,
            label=g,
            color=color_map[g]
        )

    ax.set_title(title)
    #ax.set_xlabel("Parameter value")
    cfg = x_axis_config.get(groups[0], {})

    ax.set_xlabel(cfg.get("xlabel", "Parameter value"))

    if cfg.get("xscale"):
        ax.set_xscale(cfg["xscale"])

    if cfg.get("invert"):
        ax.invert_xaxis()

    if "formatter" in cfg:
        ax.xaxis.set_major_formatter(cfg["formatter"])
        
    ax.grid(True, linestyle="--", alpha=0.6)

    if len(groups) > 1:
        ax.legend(fontsize=10)

# wspólna oś Y
axes[0].set_ylabel("Compression ratio")
axes[3].set_ylabel("Compression ratio")

plt.tight_layout()
plt.savefig("param_vs_ratio_subplots.pdf")
plt.show()


# ------------------------
# SUBPLOTS (IEEE): PARAM vs RATIO
# ------------------------
fig, axes = plt.subplots(3, 2, figsize=(7.2, 9), sharey=True)

#fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharey=True)
axes = axes.flatten()

plots = [
    (["Cloudini", "Cloudini + LZ4", "Cloudini + ZSTD"], "Cloudini"),
    (["Draco", "Draco + ZSTD"], "Draco"),
    (["Voxel"], "Voxel"),
    (["Uniform"], "Uniform"),
    (["Random"], "Random"),
    (["G-PCC"], "G-PCC"),
]

legend_handles = {}
marker_size = 6
line_width = 2.2

for ax, (groups, title) in zip(axes, plots):
    for g in groups:
        sub = df[(df['group'] == g) & (df['param_value'] > 0)]
        if sub.empty:
            continue

        line, = ax.plot(
            sub['param_value'],
            sub['ratio_mean'],
            marker='o',
            markersize=marker_size,
            linewidth=line_width,
            color=color_map[g],
            label=g
        )

        # zbieramy uchwyty tylko raz
        if g not in legend_handles:
            legend_handles[g] = line

    ax.set_title(title)
    #ax.set_xlabel("Parameter value")
    cfg = x_axis_config.get(groups[0], {})

    ax.set_xlabel(cfg.get("xlabel", "Parameter value"))

    if cfg.get("xscale"):
        ax.set_xscale(cfg["xscale"])

    if cfg.get("invert"):
        ax.invert_xaxis()

    if "formatter" in cfg:
        ax.xaxis.set_major_formatter(cfg["formatter"])
        
    ax.grid(True, linestyle="--", alpha=0.6)

    if len(groups) > 1:
        ax.legend(fontsize=10)

# wspólna oś Y
axes[0].set_ylabel("Compression ratio")
axes[3].set_ylabel("Compression ratio")

# ------------------------
# WSPÓLNA LEGENDA (IEEE)
# ------------------------
fig.legend(
    legend_handles.values(),
    legend_handles.keys(),
    loc="upper center",
    ncol=3,
    frameon=False,
    fontsize=12,
    bbox_to_anchor=(0.5, 1.03)
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("param_vs_ratio_subplots_ieee.pdf")
plt.show()


# ------------------------
# SUBPLOTS (IEEE): PARAM vs TIME
# ------------------------

fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharey=False)
axes = axes.flatten()

plots = [
    (["Cloudini", "Cloudini + LZ4", "Cloudini + ZSTD"], "Cloudini"),
    (["Draco", "Draco + ZSTD"], "Draco"),
    (["Voxel"], "Voxel"),
    (["Uniform"], "Uniform"),
    (["Random"], "Random"),
    (["G-PCC"], "G-PCC"),
]

legend_handles = {}
marker_size = 6
line_width = 2.2

for ax, (groups, title) in zip(axes, plots):
    for g in groups:
        sub = df[(df['group'] == g) & (df['param_value'] > 0)]
        if sub.empty:
            continue

        line, = ax.plot(
            sub['param_value'],
            sub['time_ms'],
            marker='o',
            markersize=marker_size,
            linewidth=line_width,
            color=color_map[g],
            label=g
        )

        # zbieramy uchwyty tylko raz
        if g not in legend_handles:
            legend_handles[g] = line

    ax.set_title(title)
    #ax.set_xlabel("Parameter value")
    cfg = x_axis_config.get(groups[0], {})

    ax.set_xlabel(cfg.get("xlabel", "Parameter value"))

    if cfg.get("xscale"):
        ax.set_xscale(cfg["xscale"])

    if cfg.get("invert"):
        ax.invert_xaxis()

    if "formatter" in cfg:
        ax.xaxis.set_major_formatter(cfg["formatter"])
        
    ax.grid(True, linestyle="--", alpha=0.6)

    if len(groups) > 1:
        ax.legend(fontsize=10)

# wspólna oś Y
axes[0].set_ylabel("Time [ms]")
axes[3].set_ylabel("Time [ms]")

# ------------------------
# WSPÓLNA LEGENDA (IEEE)
# ------------------------
fig.legend(
    legend_handles.values(),
    legend_handles.keys(),
    loc="upper center",
    ncol=3,
    frameon=False,
    fontsize=12,
    bbox_to_anchor=(0.5, 1.03)
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("param_vs_time_subplots_ieee.pdf")
plt.show()
