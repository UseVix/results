#!/usr/bin/env python3
import re
import os
import pandas as pd
import sys
from pathlib import Path
def make_data_sequnce_name_uniform(data_sequence):
    if data_sequence == "quad":
        data_sequence = "quad_easy" 
    if data_sequence == "maths":
        data_sequence = "maths_institute"
    if data_sequence == "underground":
        data_sequence = "underground_mine"
    return data_sequence
path_prefix = sys.argv[1]
df = pd.DataFrame(columns=[
    "data_sequence",
    "method",
    "byte_size",
    "encode_speed",
    "decode_speed",
    "quantization_precision"
])
def same_value(series, value):
    if pd.isna(value):
        return series.isna()
    return series == value
for root, dirs, files in os.walk(os.path.join(path_prefix,"saved_csvs")):
    for file in files:
        if file.endswith(".csv"):
            if re.search("only", file):
                continue
            file_path = os.path.join(root, file)
            encode_speed = None
            decode_speed = None
            quantization_precision = None
            with open(file_path, 'r') as f:
                lines = f.readlines()
                data_sequence = re.match(r"^[^_]+", file).group(0)
                data_sequence = make_data_sequnce_name_uniform(data_sequence)
                if len(lines) == 3:
                    topic_info = lines[2]
                    byte_size = topic_info.split(",")[-2]
                    method_match = re.search("draco|compressed", file)
                    method = method_match.group(0) if method_match else "uncompressed"
                    if method == "compressed":
                        method = "cloudini"
                    if method == "draco":
                        try:
                            encode_speed = int(re.search(r"ES:(\d+)", topic_info).group(1))
                            decode_speed = int(re.search(r"DS:(\d+)", topic_info).group(1))
                            quantization_precision = int(re.search(r"QP:(\d+)", topic_info).group(1))
                        except AttributeError:
                            print("faulty file: " + file_path)
                            print("topic_info: " + topic_info)
                            raise AttributeError("Missing expected parameters in topic_info")
                    if method == "cloudini":
                        quantization_precision = float(re.search(r"(?:cloudini|rosbag)_((?:p|\d)+)", file).group(1).replace("p", "."))
                else:
                    method = "raw_packets"
                    for line in lines:
                        found = False
                        if re.search("lidar_packets", line):
                            byte_size = line.split(",")[-2]
                            found = True
                            break
                    if not found:
                        continue
            df.loc[len(df)] = {
                "data_sequence": data_sequence,
                "method": method,
                "byte_size": byte_size,
                "encode_speed": encode_speed if method == "draco" else None,
                "decode_speed": decode_speed if method == "draco" else None,
                "quantization_precision": (
                    quantization_precision
                    if method in ["draco", "cloudini"] else None
                ),
                "gigabyte_size": None
            }
for root, dirs, files in os.walk(path_prefix):
    if root.startswith("./LIORF"):
        continue
    for file in files:
        if file.endswith("saved_sizes.txt"):
            file_path = Path(os.path.join(root, file))
            with open(str(file_path), 'r') as f:
                lines = f.readlines()
                for file_name,size in zip(lines[::2],lines[1::2]):
                    data_sequence = file_path.parent.name
                    data_sequence = make_data_sequnce_name_uniform(data_sequence)
                    try:
                        method = re.search("draco|compressed|only", file_name).group(0)
                    except AttributeError:
                        print("faulty file: " + str(file_path))
                        print("file_name: " + file_name)
                        raise AttributeError("Missing expected parameters in file_name")
                    if method == "only":
                        method = "raw_packets"
                    if method == "raw_packets":
                        encode_speed = None
                        decode_speed = None
                        quantization_precision = None
                    if method == "compressed":
                        encode_speed = None
                        decode_speed = None
                        method = "cloudini"
                        quantization_precision = float(re.search(r"(?:cloudini|rosbag)_((?:p|\d)+)", file_name).group(1).replace("p", "."))
                    if method == "draco":
                        try:
                            parameters_list = re.search(r"draco_ros2_(\d+)_(\d+)_(\d+)", file_name).groups()
                        except AttributeError:
                            print("faulty file: " + str(file_path))
                            print("file_name: " + file_name)
                            raise AttributeError("Missing expected parameters in file_name")
                        encode_speed = int(parameters_list[0])
                        decode_speed = int(parameters_list[1])
                        quantization_precision = int(parameters_list[2])
                    gigabyte_size = re.match(r"^Bag size:\s+([^\s]+)", size).group(1)
                    mask = (
                        (df["data_sequence"] == data_sequence)
                        & (df["method"] == method)
                        & same_value(df["quantization_precision"], quantization_precision)
                        & same_value(df["encode_speed"], encode_speed)
                        & same_value(df["decode_speed"], decode_speed)
                    )
                    found_count = mask.sum()
                    print("Counted matches " + str(found_count))
                    if found_count != 1:
                        print("#################################")
                        YELLOW = "\033[93m"
                        RESET = "\033[0m"
                        print(f"{YELLOW}Warning: Found {found_count} matches for data_sequence={data_sequence}, method={method}, quantization_precision={quantization_precision}, encode_speed={encode_speed}, decode_speed={decode_speed}. Expected exactly 1 match.{RESET}")
                        print("#################################")
                    
                    if found_count == 0:
                        print("#################################")
                        YELLOW = "\033[93m"
                        RESET = "\033[0m"
                        print(f"{YELLOW}Warning: Adding new entry for data_sequence={data_sequence}, method={method}, quantization_precision={quantization_precision}, encode_speed={encode_speed}, decode_speed={decode_speed} with gigabyte_size={gigabyte_size}.{RESET}")

                        df.loc[len(df)] = {
                            "data_sequence": data_sequence,
                            "method": method,
                            "byte_size": None,
                            "encode_speed": encode_speed if method == "draco" else None,
                            "decode_speed": decode_speed if method == "draco" else None,
                            "quantization_precision": (
                                quantization_precision
                                if method in ["draco", "cloudini"] else None
                            ),
                            "gigabyte_size": gigabyte_size
                        }
                        print("#################################")
                    
                    if found_count > 0:
                        df.loc[mask, "gigabyte_size"] = gigabyte_size
               
output_csv_path = os.path.join(path_prefix, "summary.csv")
if not os.path.exists(output_csv_path):
    df.to_csv(output_csv_path, index=False)
elif not df.empty:
    print(f"Summary CSV already exists for {root}. Skipping.")