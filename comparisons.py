#!/usr/bin/env python3
import pandas as pd
import numpy as np

def run_comparisons(csv_path="merged_outer_with_kc.csv"):
    df = pd.read_csv(csv_path)

    # 1. Base Filtering
    df = df[df["slam_method"] != "LIORF"]
    
    # Ensure byte_size exists
    if "byte_size" not in df.columns and "gigabyte_size" in df.columns:
        mask = df["byte_size"].isna() & df["gigabyte_size"].notna()
        df.loc[mask, "byte_size"] = df.loc[mask, "gigabyte_size"] * (1024**3)

    # 2. Get uncompressed sizes to calculate the compression ratio
    uncompressed_df = df[df["method"] == "uncompressed"][["data_sequence", "slam_method", "byte_size"]]
    uncompressed_df = uncompressed_df.groupby(["data_sequence", "slam_method"])["byte_size"].mean().reset_index()
    uncompressed_df.rename(columns={"byte_size": "uncompressed_size"}, inplace=True)

    df = df.merge(uncompressed_df, on=["data_sequence", "slam_method"], how="left")

    # 3. Calculate Compression Ratio
    df["compression_ratio"] = df["byte_size"] / df["uncompressed_size"]

    # Separate methods based on your constraints
    cloudini_full = df[df["method"] == "cloudini"]
    draco_full = df[(df["method"] == "draco") & (df["encode_speed"] == 10) & (df["decode_speed"] == 10)]
    uncompressed_full = df[df["method"] == "uncompressed"]

    # Counters for final tally
    tallies = {
        "Closest Ratio -> Compare RMSE": {"draco": 0, "cloudini": 0, "tie": 0},
        "Closest Ratio -> Compare Max Error": {"draco": 0, "cloudini": 0, "tie": 0},
        "Closest RMSE -> Compare Ratio": {"draco": 0, "cloudini": 0, "tie": 0},
        "Closest Max Error -> Compare Ratio": {"draco": 0, "cloudini": 0, "tie": 0}
    }

    # Counters for uncompressed baseline check (grouped by SLAM method)
    uncompressed_checks = {
        "rmse": {},
        "max": {}
    }

    # Helper function to find closest match and compare
    def find_and_compare(group_name, c_df, d_df, match_col, compare_col, comparison_name):
        c_clean = c_df.dropna(subset=[match_col, compare_col])
        d_clean = d_df.dropna(subset=[match_col, compare_col])
        
        if c_clean.empty or d_clean.empty:
            return

        cross = c_clean.assign(key=1).merge(d_clean.assign(key=1), on="key", suffixes=("_c", "_d"))
        cross["match_diff"] = (cross[f"{match_col}_c"] - cross[f"{match_col}_d"]).abs()
        
        best_match = cross.loc[cross["match_diff"].idxmin()]

        val_c = best_match[f"{compare_col}_c"]
        val_d = best_match[f"{compare_col}_d"]
        diff = abs(val_c - val_d)

        if val_c < val_d:
            winner, loser, win_val = "cloudini", "draco", val_c
        elif val_d < val_c:
            winner, loser, win_val = "draco", "cloudini", val_d
        else:
            winner = "tie"
            
        tallies[comparison_name][winner] += 1

        print(f"  [{comparison_name}]")
        print(f"    - Closest pair on {match_col}:")
        print(f"      Cloudini (Prec {best_match['quantization_precision_c']}): {best_match[f'{match_col}_c']:.5f}")
        print(f"      Draco (Prec {int(best_match['quantization_precision_d'])}): {best_match[f'{match_col}_d']:.5f}")
        print(f"      (Difference: {best_match['match_diff']:.5f})")
        
        if winner == "tie":
            print(f"    - Result on {compare_col}: TIE at {val_c:.5f}")
        else:
            print(f"    - Result on {compare_col}: {winner.upper()} wins ({val_c:.5f} vs {val_d:.5f}) | Diff: {diff:.5f}")
        print()

    # Loop through all sequence/slam pairs
    grouped = df.groupby(["data_sequence", "slam_method"])
    for (seq, slam), group in grouped:
        c_subset = cloudini_full[(cloudini_full["data_sequence"] == seq) & (cloudini_full["slam_method"] == slam)]
        d_subset = draco_full[(draco_full["data_sequence"] == seq) & (draco_full["slam_method"] == slam)]
        u_subset = uncompressed_full[(uncompressed_full["data_sequence"] == seq) & (uncompressed_full["slam_method"] == slam)]

        # Check Uncompressed Baseline Performance Grouped by SLAM
        if not u_subset.empty:
            for metric in ["rmse", "max"]:
                if slam not in uncompressed_checks[metric]:
                    uncompressed_checks[metric][slam] = {"lowest": 0, "not_lowest": 0}
                
                u_val = u_subset[metric].min()
                if pd.notna(u_val):
                    group_min = group[metric].min()
                    if u_val <= group_min:
                        uncompressed_checks[metric][slam]["lowest"] += 1
                    else:
                        uncompressed_checks[metric][slam]["not_lowest"] += 1

        if c_subset.empty or d_subset.empty:
            continue

        print(f"==================================================")
        print(f"Sequence: {seq} | SLAM: {slam}")
        print(f"==================================================")

        find_and_compare(seq, c_subset, d_subset, "compression_ratio", "rmse", "Closest Ratio -> Compare RMSE")
        find_and_compare(seq, c_subset, d_subset, "compression_ratio", "max", "Closest Ratio -> Compare Max Error")
        find_and_compare(seq, c_subset, d_subset, "rmse", "compression_ratio", "Closest RMSE -> Compare Ratio")
        find_and_compare(seq, c_subset, d_subset, "max", "compression_ratio", "Closest Max Error -> Compare Ratio")

    # Final Summary Output
    print("==================================================")
    print("FINAL WIN TALLIES")
    print("==================================================")
    for comparison, counts in tallies.items():
        total = sum(counts.values())
        print(f"{comparison} (Total Valid Matches: {total})")
        print(f"  - Draco wins:    {counts['draco']}")
        print(f"  - Cloudini wins: {counts['cloudini']}")
        print(f"  - Ties:          {counts['tie']}")
        print()

    print("==================================================")
    print("UNCOMPRESSED BASELINE INTEGRITY CHECK")
    print("==================================================")
    for metric, slam_dict in uncompressed_checks.items():
        for slam, checks in slam_dict.items():
            total_checked = checks['lowest'] + checks['not_lowest']
            print(f"{metric.upper()} | {slam} (Total Checked: {total_checked})")
            print(f"  - Uncompressed was the lowest error:     {checks['lowest']} times")
            print(f"  - A compressed method had a lower error: {checks['not_lowest']} times")
            print()

if __name__ == "__main__":
    run_comparisons("merged_outer_with_kc.csv")