#!/usr/bin/env python3

import os
from pathlib import Path
import re
import pandas as pd
import sys
from evo.tools import file_interface
path_prefix = sys.argv[1]
df = pd.DataFrame(columns=[
    "data_sequence",
    "method",
    "encode_speed",
    "decode_speed",
    "quantization_precision",
    "slam_method",
    "rmse",
    "mean",
    "median",
    "std",
    "min",
    "max",
    "sse"
])
for root, dirs, files in os.walk(path_prefix):
    for file in files:
        if file.endswith("_tum"):
            data = file_interface.load_res_file(os.path.join(root, file)).stats
            folder = Path(root).parts
            data['slam_method'] = folder[-5]
            data['data_sequence'] = folder[-3]
            data['method'] = folder[-2]
            method = data['method']
            groups = re.search(r"ros2_(\d+)_(\d+)_(\d+)", file)
            if re.search("(sequentially|uncompressed)", file):
                continue
            if method == "draco" and groups is None:
                try:
                    data['encode_speed'] = int(re.search(r"ES[:|_](\d+)", file).group(1))
                    data['decode_speed'] = int(re.search(r"DS[:|_](\d+)", file).group(1))
                    data['quantization_precision'] = int(re.search(r"QP[:|_](\d+)", file).group(1))
                except AttributeError:
                    print("faulty file: " + str(file))
                    print("method: " + method)
                    raise AttributeError("Missing expected parameters in file name")
            if method == "draco" and groups is not None and len(groups.groups()) == 3:
                parameter_groups = groups.groups()
                data['encode_speed'] = int(parameter_groups[0])
                data['decode_speed'] = int(parameter_groups[1])
                data['quantization_precision'] = int(parameter_groups[2])
            if method == "cloudini":
                data['encode_speed'] = None
                data['decode_speed'] = None
                try:
                    data['quantization_precision'] = float(re.search(r"(?:cloudini|rosbag)_((?:p|\d)+)", file).group(1).replace("p", ".")) 
                except AttributeError:
                    print("faulty file: " + str(file))
                    print("method: " + method)
                    raise AttributeError("Missing expected parameters in file name")
            if not type(data['quantization_precision']) in [int, float]:
                raise ValueError(f"quantization_precision should be int or float, but got {type(data['quantization_precision'])} for file {file}")
            df.loc[len(df)] = data
output_csv_path = os.path.join(path_prefix, "summary_evo.csv")
if not os.path.exists(output_csv_path):
    df.to_csv(output_csv_path, index=False)
    print(f"Summary CSV created at {output_csv_path}.")
elif not df.empty:
    print(f"Summary CSV already exists for {root}. Skipping.")
