#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import os
from adjustText import adjust_text
import plotly.graph_objects as go
# Sequence durations (in seconds)
DURATIONS = {
    "quad_easy": 198,
    "maths_institute": 216, 
    "cloister": 278,
    "stairs": 118,
    "park": 1567,
    "campus": 1383,
    "ciampino": 3688,
    "colosseo": 1827,
    "pincio": 2064,
    "spagna": 1458,
    "diag": 1400,            
    "underground_mine": 120  
}

def generate_graphs(csv_path="merged_outer_with_kc.csv"):
    df = pd.read_csv(csv_path)

    # 1. Filter out liorf
    df = df[df["slam_method"] != "LIORF"]

    # 2. Ensure byte_size exists
    if "byte_size" not in df.columns and "gigabyte_size" in df.columns:
        df["byte_size"] = df["gigabyte_size"] * (1024**3)
    df.loc[df["byte_size"].isna() & df["gigabyte_size"].notna(), "byte_size"] = df.loc[df["byte_size"].isna(), "gigabyte_size"] * (1024**3)
    print(df[(df["data_sequence"]=="park") & (df["method"]=="draco") & (df["encode_speed"]==10) & (df["decode_speed"]==10) & (df["quantization_precision"]==9)])

    # 3. Calculate Uncompressed Baseline
    uncompressed_df = df[df["method"] == "uncompressed"][["data_sequence", "byte_size"]]
    uncompressed_df = uncompressed_df.groupby(["data_sequence"])["byte_size"].mean().reset_index()
    uncompressed_df.rename(columns={"byte_size": "uncompressed_size"}, inplace=True)
    df = df.merge(uncompressed_df, on=["data_sequence"], how="left")

    # 4. Calculate Metrics
    df["compression_ratio"] =  df["byte_size"] / df["uncompressed_size"]
    df["duration"] = df["data_sequence"].map(DURATIONS).fillna(200) 
    df["avg_bandwidth_mbps"] = (df["byte_size"] / (1024 * 1024)) / df["duration"]

    os.makedirs("slam_graphs", exist_ok=True)

    x_variants = [
        ("compression_ratio", "Compression Ratio")
        #,("avg_bandwidth_mbps", "Average Bandwidth (MB/s)")
    ]
    y_variants = [
        ("rmse", "RMSE [m]"),
        ("max", "Max Error [m]")
    ]

    grouped = df.groupby(["data_sequence", "slam_method"])

    for (seq, slam), group in grouped:
        cloudini = group[group["method"] == "cloudini"]
        draco = group[(group["method"] == "draco") & (group["encode_speed"] == 10) & (group["decode_speed"] == 10)]
        uncompressed = group[group["method"] == "uncompressed"]

        for x_col, x_label in x_variants:
            for y_col, y_label in y_variants:
                fig = go.Figure()

                # Plot Uncompressed (Grey)
                if not uncompressed.empty:
                    valid_uncompressed = uncompressed.dropna(subset=[x_col, y_col])
                    if not valid_uncompressed.empty:
                        fig.add_trace(go.Scatter(
                            x=valid_uncompressed[x_col],
                            y=valid_uncompressed[y_col],
                            mode='markers',
                            marker=dict(color='grey', size=14, symbol='star'),
                            name='Uncompressed'
                        ))

                # Plot Cloudini (Blue)
                if not cloudini.empty:
                    valid_cloudini = cloudini.dropna(subset=[x_col, y_col])
                    if not valid_cloudini.empty:
                        fig.add_trace(go.Scatter(
                            x=valid_cloudini[x_col],
                            y=valid_cloudini[y_col],
                            mode='markers+text',
                            marker=dict(color='blue', size=10, opacity=0.7),
                            text=[str(p) if pd.notna(p) else "" for p in valid_cloudini["quantization_precision"]],
                            textposition="top center",
                            textfont=dict(color="darkblue", size=11),
                            name='Cloudini'
                        ))

                # Plot Draco (Red)
                if not draco.empty:
                    valid_draco = draco.dropna(subset=[x_col, y_col])
                    if not valid_draco.empty:
                        fig.add_trace(go.Scatter(
                            x=valid_draco[x_col],
                            y=valid_draco[y_col],
                            mode='markers+text',
                            marker=dict(color='red', size=10, opacity=0.7),
                            # Safely convert to int to drop the .0
                            text=[str(int(p)) if pd.notna(p) else "" for p in valid_draco["quantization_precision"]],
                            textposition="top center",
                            textfont=dict(color="darkred", size=11),
                            name='Draco (Speed 10)'
                        ))

                # Formatting and titles
                fig.update_layout(
                    title=f"Sequence: {seq} | SLAM: {slam}<br>{y_label} vs {x_label}",
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    template="plotly_white",
                    hovermode="closest"
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', zeroline=True, zerolinecolor='lightgray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', zeroline=True, zerolinecolor='lightgray')

                # Configure the export button to download a high-res PNG
                clean_seq = str(seq).replace("/", "_").replace(" ", "_")
                clean_slam = str(slam).replace("/", "_").replace(" ", "_")
                
                config = {
                    'toImageButtonOptions': {
                        'format': 'png', # Ensures PNG export
                        'filename': f"{clean_seq}_{clean_slam}_{x_col}_{y_col}_zoomed",
                        'scale': 3 # Multiplies resolution by 3 for a crisp image
                    },
                    'displayModeBar': True # Ensures the toolbar is always accessible
                }

                # Save as interactive HTML
                file_name = f"slam_graphs/{clean_seq}_{clean_slam}_{x_col}_{y_col}.html"
                fig.write_html(file_name, config=config)

    print("All graphs successfully generated in the 'slam_graphs' folder as HTMLs.")

if __name__ == "__main__":
    generate_graphs("merged_outer_with_kc.csv")