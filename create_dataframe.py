#!/usr/bin/env python3
import re
import os
import pandas as pd
path_prefix = "/seagate_dataset/NewerCollege/"
df = pd.DataFrame(columns=[
    "data_sequence",
    "method",
    "byte_size",
    "encode_speed",
    "decode_speed",
    "quantization_precision"
])
for root, dirs, files in os.walk(path_prefix):
    for file in files:
        if file.endswith(".csv"):
            file_path = os.path.join(root, file)
            encode_speed = None
            decode_speed = None
            quantization_precision = None
            with open(file_path, 'r') as f:
                lines = f.readlines()
                data_sequence = re.match(r"^[^_]+", file).group(0)
                if len(lines) == 3:
                    topic_info = lines[2]
                    byte_size = topic_info.split(",")[-2]
                    method_match = re.search("draco|compressed", topic_info)
                    method = method_match.group(0) if method_match else "uncompressed"
                    if method == "compressed":
                        method = "cloudini"
                    if method == "draco":
                        encode_speed = int(re.search("ES:(\d)+", topic_info).group(1))
                        decode_speed = int(re.search("DS:(\d)+", topic_info).group(1))
                        quantization_precision = int(re.search("QP:(\d)+", topic_info).group(1))
                    if method == "cloudini":
                        quantization_precision = float(re.search("0p\d+", file).group(0).replace("p", "."))
                else:
                    method = "raw_packets"
                    for line in lines:
                        if re.search("raw_packets", line):
                            byte_size = line.split(",")[-2]
                            break
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
    if root.endswith("LIORF"):
        continue
    for file in files:
        if file.endswith("saved_sizes.txt"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for file_name,size in zip(lines[::2],lines[1::2]):
                    data_sequence = file_path.parent.name
                    method = re.search("draco|compressed", file_name).group(0)
                    if method == "compressed":
                        encode_speed = None
                        decode_speed = None
                        method = "cloudini"
                        quantization_precision = float(re.search("0p\d+", file_name).group(0).replace("p", "."))
                    if method == "draco":
                        parameters_list = re.search(r"draco_ros2_(\d+)_(\d+)_(\d+)", file_name).groups()
                        encode_speed = int(parameters_list[0])
                        decode_speed = int(parameters_list[1])
                        quantization_precision = int(parameters_list[2])
                    gigabyte_size = re.match(r"^Bag size:\s+([^\s]+)", size).group(1)
                    mask = ((df["data_sequence"] == data_sequence) & 
                           (df["method"] == method) & 
                           (df["quantization_precision"] == quantization_precision) & 
                           (df["encode_speed"] == encode_speed) & 
                           (df["decode_speed"] == decode_speed))
                    found_count = mask.sum()
                    print("Counted matches " + str(found_count))
                    if found_count != 1:
                        print("#################################")
                        YELLOW = "\033[93m"
                        RESET = "\033[0m"
                        print(f"{YELLOW}Warning: Found {found_count} matches for data_sequence={data_sequence}, method={method}, quantization_precision={quantization_precision}, encode_speed={encode_speed}, decode_speed={decode_speed}. Expected exactly 1 match.{RESET}")
                        print("#################################")
                    df.loc[mask, "gigabyte_size"] = gigabyte_size
               
output_csv_path = os.path.join(path_prefix, "summary.csv")
if not os.path.exists(output_csv_path):
    df.to_csv(output_csv_path, index=False)
elif not df.empty:
    print(f"Summary CSV already exists for {root}. Skipping.")