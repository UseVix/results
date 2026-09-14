#!/usr/bin/env python3
import pandas as pd
columns = ["data_sequence","method","quantization_precision","slam_method","rmse","max","encode_speed","decode_speed","byte_size"]

left=pd.read_csv("merged_outer.csv")
right=pd.read_csv("kc_slam_compression_stats.csv")
#print("Left columns:", left.loc["data_sequence"])
#print("Right columns:", right.loc["data_sequence"])
print("my data_sequence unique values:", left["data_sequence"].unique())
print("kc_slam_compression_stats data_sequence unique values:", right["data_sequence"].unique())




print("NA values in right dataframe before replacement:", len(right.loc[right["quantization_precision"].isna(), "method"]))
right.loc[right["quantization_precision"].isna(), "method"]="uncompressed"
right.loc[right["method"]=="draco", ["encode_speed","decode_speed"]]=[10,10]
right.loc[right["method"]=="cloudini", ["encode_speed","decode_speed"]]=[None,None]

left["data_sequence"]=left["data_sequence"].str.lower()
right['data_sequence'] = right['data_sequence'].str.removesuffix('_ros2')
right.loc[right["data_sequence"]=="maths_easy", "data_sequence"]="maths_institute"
right.loc[right["data_sequence"]=="underground_easy", "data_sequence"]="underground_mine"


print("Right columns")
print(right.columns)
print(right[["data_sequence","method","encode_speed","decode_speed","quantization_precision"]])
right_argument=right[["data_sequence","method","encode_speed","decode_speed","quantization_precision"]]
seq_val, method_val, enc_val, dec_val, quant_val = right_argument

mask = (
    (left["data_sequence"] == seq_val) & 
    (left["method"] == method_val) & 
    (left["encode_speed"] == enc_val) & 
    (left["decode_speed"] == dec_val) & 
    (left["quantization_precision"] == quant_val)
)

left_for_arguments = left.loc[mask, "byte_size"]
print("Left nyte_size")
print(left_for_arguments)
merge_cols = ["data_sequence", "method", "encode_speed", "decode_speed", "quantization_precision"]

right = right.merge(
    left[merge_cols + ["byte_size"]], 
    on=merge_cols, 
    how="left"
)

sus_left=left[(left["encode_speed"]==10) & (left["decode_speed"]==10) & (left["method"]=="uncompressed")]
sus_right=right[(right["encode_speed"]==10) & (right["decode_speed"]==10) & (right["method"]=="uncompressed")]
print("Sus Left:",sus_left)
print("Sus Right:",sus_right)
print(left["data_sequence"].unique())
print(right["data_sequence"].unique())
merged=left.merge(right, how="outer", on=columns)
merged.to_csv("merged_outer_with_kc.csv", index=False)
print(merged[(merged["data_sequence"]=="park") & (merged["method"]=="draco") & (merged["encode_speed"]==10) & (merged["decode_speed"]==10) & (merged["quantization_precision"]==9)])
#print(merged[(merged["data_sequence"]=="maths") & (merged["method"]=="draco") & (merged["encode_speed"]==10) & (merged["decode_speed"]==10) & (merged["quantization_precision"]==9)])

print("Succesfully merged kc_slam_compression_stats.csv with merged_outer.csv and saved as merged_outer_with_kc.csv")